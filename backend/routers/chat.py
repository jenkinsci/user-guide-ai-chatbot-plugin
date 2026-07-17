from fastapi import APIRouter, Depends, HTTPException, status, Query
from routers.auth import get_current_user, User
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_database_session
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
import schemas
from datetime import datetime, timezone
import models

router = APIRouter(prefix="/chats", tags=["Chats Management"])


@router.post(
    "/", response_model=schemas.ChatResponse, status_code=status.HTTP_201_CREATED
)
async def create_new_chat(
    chat_data: schemas.ChatCreateRequest,
    db_session: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a new chat session linked to the authenticated user.
    """
    new_chat_record = models.ChatEntity(title=chat_data.title, user_id=current_user.id)

    db_session.add(new_chat_record)
    await db_session.commit()

    await db_session.refresh(new_chat_record)

    return new_chat_record


@router.get("/", response_model=schemas.PaginatedChatResponse)
async def get_my_chats(
    limit: int = Query(
        20, ge=1, le=100, description="Number of chats to return per page"
    ),
    offset: int = Query(0, ge=0, description="Number of chats to skip"),
    db_session: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves the paginated list of active chats belonging to the authenticated user.
    Ordered by the most recently updated chats first.
    Strictly filters out soft-deleted chats.
    """
    count_query = select(func.count(models.ChatEntity.id)).where(
        models.ChatEntity.user_id == current_user.id,
        models.ChatEntity.deleted_at.is_(None),
    )
    total_chats = (await db_session.execute(count_query)).scalar_one()

    query = (
        select(models.ChatEntity)
        .where(
            models.ChatEntity.user_id == current_user.id,
            models.ChatEntity.deleted_at.is_(None),
        )
        .order_by(models.ChatEntity.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )

    paginated_results = (await db_session.execute(query)).scalars().all()

    return schemas.PaginatedChatResponse(
        items=list(paginated_results),
        total_items=total_chats,
        limit=limit,
        offset=offset,
    )


@router.get("/{chat_id}", response_model=schemas.PaginatedQAResponse)
async def get_chat_history(
    chat_id: int,
    limit: int = Query(
        20, ge=1, le=100, description="Number of messages to return per page"
    ),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    db_session: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves the paginated history of a specific chat.
    Messages are ordered from the newest to the oldest.
    """
    # Verify that the chat exists, belongs to the user, and is not soft-deleted
    chat_validation_query = select(models.ChatEntity).where(
        models.ChatEntity.id == chat_id,
        models.ChatEntity.user_id == current_user.id,
        models.ChatEntity.deleted_at.is_(None),
    )
    target_chat = (await db_session.execute(chat_validation_query)).scalars().first()

    if not target_chat:
        raise HTTPException(status_code=404, detail="Chat not found or access denied.")

    # Count the total number of active QA pairs for this chat
    count_query = select(func.count(models.QAPairEntity.id)).where(
        models.QAPairEntity.chat_id == chat_id, models.QAPairEntity.deleted_at.is_(None)
    )
    total_messages = (await db_session.execute(count_query)).scalar_one()

    # Fetch the paginated QA pairs
    history_query = (
        select(models.QAPairEntity)
        .options(
            selectinload(models.QAPairEntity.question),
            selectinload(models.QAPairEntity.answer),
        )
        .where(
            models.QAPairEntity.chat_id == chat_id,
            models.QAPairEntity.deleted_at.is_(None),
        )
        .order_by(models.QAPairEntity.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    paginated_results = (await db_session.execute(history_query)).scalars().all()

    return schemas.PaginatedQAResponse(
        items=list(paginated_results),
        total_items=total_messages,
        limit=limit,
        offset=offset,
    )


@router.put("/{chat_id}/title", response_model=schemas.ChatResponse)
async def update_chat_title(
    chat_id: int,
    payload: schemas.ChatTitleUpdateRequest,
    db_session: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
):
    """
    Updates the title of a specific chat.
    """
    query = select(models.ChatEntity).where(
        models.ChatEntity.id == chat_id,
        models.ChatEntity.user_id == current_user.id,
        models.ChatEntity.deleted_at.is_(None),
    )

    execution_result = await db_session.execute(query)
    target_chat = execution_result.scalars().first()

    if not target_chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or access denied.",
        )

    target_chat.title = payload.new_title

    await db_session.commit()
    await db_session.refresh(target_chat)

    return target_chat


@router.delete("/{chat_id}", status_code=status.HTTP_200_OK)
async def soft_delete_chat(
    chat_id: int,
    db_session: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
):
    """
    Performs a soft delete on a specific chat by setting the deleted_at timestamp.
    """
    query = select(models.ChatEntity).where(
        models.ChatEntity.id == chat_id,
        models.ChatEntity.user_id == current_user.id,
        models.ChatEntity.deleted_at.is_(None),
    )

    execution_result = await db_session.execute(query)
    target_chat = execution_result.scalars().first()

    if not target_chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or already deleted.",
        )

    target_chat.deleted_at = datetime.now(timezone.utc)

    await db_session.commit()

    return {"message": f"Chat {chat_id} successfully deleted."}
