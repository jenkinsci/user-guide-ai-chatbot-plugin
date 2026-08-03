from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from routers.auth import get_current_user, User
from database import get_database_session
import schemas
from langchain_qdrant import QdrantVectorStore
from vectordb.vector_store import get_vector_store
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List
import models
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from qdrant_client.http import models as qmodels

router = APIRouter(prefix="/context", tags=["Chats Management"])


async def manage_logs(
    logs_content: str | None, vector_store: QdrantVectorStore, chat_id: int
) -> bool:

    try:
        # Delete previous logs
        vector_store.client.delete(
            collection_name=vector_store.collection_name,
            points_selector=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="metadata.chat_id", match=qmodels.MatchValue(value=chat_id)
                    )
                ]
            ),
        )

        if not logs_content:
            return False

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            separators=[
                r"\n(?=\[Pipeline\] stage)",  # 1. Prioritize splitting at new Jenkins stages
                r"\n(?=\[?(?:ERROR|FATAL|Exception))",  # 2. Keep errors at the start of a chunk
                r"\n(?=\[?\d{4}-\d{2}-\d{2})",  # 3. Date timestamps (e.g., [2026-07-12)
                r"\n(?=\[?\d{2}:\d{2}:\d{2})",  # 4. Time timestamps (e.g., 14:32:01)
                "\n\n",  # 5. Fallback: double newline
                "\n",  # 6. Fallback: single newline
                " ",  # 7. Absolute fallback: spaces
            ],
            is_separator_regex=True,
        )

        raw_chunks: List[str] = text_splitter.split_text(logs_content)
        documents: List[Document] = []

        for index, chunk in enumerate(raw_chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "chat_id": chat_id,
                    "chunk_index": index,
                    "source": "jenkins_build_log",
                },
            )
            documents.append(doc)

        if documents:
            await vector_store.aadd_documents(documents)

        return True

    except Exception as e:
        print(f"Failed to chunk and store logs in Qdrant.")
        return False


async def store_context(
    db_session: AsyncSession,
    user_id: str,
    chat_id: int,
    context: schemas.JenkinsContext,
    vector_store: QdrantVectorStore,
) -> bool:
    try:
        stmt = (
            select(models.ChatEntity)
            .options(selectinload(models.ChatEntity.context))
            .where(
                models.ChatEntity.id == chat_id,
                models.ChatEntity.user_id == user_id,
                models.ChatEntity.deleted_at.is_(None),
            )
        )
        result = await db_session.execute(stmt)
        target_chat = result.scalars().first()

        if not target_chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found or already deleted.",
            )

        logs_content = None

        # Vectorize and store logs in Qdrant if they exist
        if context.build_details and context.build_details.console_log_tail:
            logs_content = context.build_details.console_log_tail

        build_log_stored = await manage_logs(logs_content, vector_store, chat_id)

        context_data = context.model_dump(exclude_none=True)

        if (
            "build_details" in context_data
            and "console_log_tail" in context_data["build_details"]
        ):
            del context_data["build_details"]["console_log_tail"]

        if target_chat.context:
            await db_session.delete(target_chat.context)
            await db_session.flush()

        new_context = models.ContextEntity(
            build_log_stored=build_log_stored,
            current_screen=context_data.get("current_screen"),
            root_url=context_data.get("root_url"),
            system_message=context_data.get("system_message"),
            agent_stats=context_data.get("agent_stats"),
            jenkins_version=context_data.get("jenkins_version"),
            active_plugins=context_data.get("active_plugins"),
            master_node=context_data.get("master_node"),
            job_details=context_data.get("job_details"),
            build_details=context_data.get("build_details"),
        )

        target_chat.context = new_context

        await db_session.commit()
        return True

    except Exception as e:
        await db_session.rollback()
        print(f"Failed to store context for chat {chat_id}: {str(e)}")
        raise e


@router.post(
    "/{chat_id}/",
    response_model=schemas.ContextResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_context(
    chat_id: int,
    payload: schemas.UploadContext,
    db_session: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
):
    vector_store = get_vector_store()

    await store_context(
        db_session, str(current_user.id), chat_id, payload.jenkins_context, vector_store
    )

    return schemas.ContextResponse(success=True, received_data=payload.jenkins_context)


@router.get(
    "/{chat_id}/last-upload",
    response_model=schemas.LastContextUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def get_last_context_upload(
    chat_id: int,
    db_session: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(models.ChatEntity)
        .options(selectinload(models.ChatEntity.context))
        .where(
            models.ChatEntity.id == chat_id,
            models.ChatEntity.user_id == current_user.id,
            models.ChatEntity.deleted_at.is_(None),
        )
    )
    result = await db_session.execute(stmt)
    target_chat = result.scalars().first()

    if not target_chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or already deleted.",
        )

    if target_chat.context:
        return schemas.LastContextUploadResponse(
            last_upload_at=target_chat.context.updated_at
        )

    return schemas.LastContextUploadResponse(last_upload_at=None)
