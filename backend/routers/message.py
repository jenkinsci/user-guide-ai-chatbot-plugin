import models
import schemas
from database import get_database_session
from routers.auth import get_current_user, User
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi.responses import StreamingResponse
from sqlalchemy import update
import json
import asyncio

router = APIRouter(prefix="/messages", tags=["Messages & Generation"])


async def generate_ai_answer_stream(question_text: str):
    """
    Mock generator representing a streaming response from an LLM.
    Yields words one by one to simulate typing.
    """
    mock_response = f"This is an automated streaming response to: '{question_text}'"
    words = mock_response.split(" ")
    
    for word in words:
        await asyncio.sleep(0.1) 
        yield word + " "


async def soft_delete_subsequent_history(
    db_session: AsyncSession, 
    chat_id: int, 
    target_timestamp: datetime
):
    """
    Soft-deletes all QAPairs (and their questions/answers) in a chat 
    that were created at or after the target timestamp.
    """
    now_utc = datetime.now(timezone.utc)
    
    # Query all the QAPair more recent than the target timestamp
    query = select(models.QAPairEntity).where(
        models.QAPairEntity.chat_id == chat_id,
        models.QAPairEntity.created_at >= target_timestamp,
        models.QAPairEntity.deleted_at.is_(None)
    )
    
    result = await db_session.execute(query)
    qa_pairs_to_delete = result.scalars().all()
    
    if not qa_pairs_to_delete:
        return

    qa_pair_ids = [qa.id for qa in qa_pairs_to_delete]
    
    # Bulk update deleted_at for the QA pairs, questions, and answers
    await db_session.execute(
        update(models.QAPairEntity)
        .where(models.QAPairEntity.id.in_(qa_pair_ids))
        .values(deleted_at=now_utc)
    )
    
    await db_session.execute(
        update(models.QuestionEntity)
        .where(models.QuestionEntity.qa_pair_id.in_(qa_pair_ids))
        .values(deleted_at=now_utc)
    )
    
    await db_session.execute(
        update(models.AnswerEntity)
        .where(models.AnswerEntity.qa_pair_id.in_(qa_pair_ids))
        .values(deleted_at=now_utc)
    )


@router.post("/send")
async def send_message_stream(
    payload: schemas.MessageSendRequest,
    db_session: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """
    Standard chat flow using Server-Sent Events (SSE).
    Saves the question, streams the AI reply, and saves the final answer.
    """
    # Verify chat exists and belongs to the active user
    chat_query = select(models.ChatEntity).where(
        models.ChatEntity.id == payload.chat_id,
        models.ChatEntity.user_id == current_user.id,
        models.ChatEntity.deleted_at.is_(None)
    )
    chat = (await db_session.execute(chat_query)).scalars().first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found or access denied.")

    # Create the QA Pair and Question
    new_qa_pair = models.QAPairEntity(chat_id=chat.id)
    db_session.add(new_qa_pair)
    await db_session.flush()
    
    new_question = models.QuestionEntity(
        qa_pair_id=new_qa_pair.id,
        content=payload.content
    )
    db_session.add(new_question)
    
    await db_session.commit()

    async def sse_generator():
        accumulated_answer = ""
        
        try:
            # Send an initial event to let the frontend know the IDs
            initial_metadata = {
                "event": "started",
                "qa_pair_id": new_qa_pair.id
            }
            yield f"data: {json.dumps(initial_metadata)}\n\n"

            # Stream chunks from the AI model
            async for chunk in generate_ai_answer_stream(payload.content):
                accumulated_answer += chunk
                
                chunk_data = {"event": "chunk", "content": chunk}
                yield f"data: {json.dumps(chunk_data)}\n\n"

            # Once generation is fully complete, save the answer to the database
            new_answer = models.AnswerEntity(
                qa_pair_id=new_qa_pair.id,
                content=accumulated_answer
            )
            db_session.add(new_answer)
            await db_session.commit()

            # Send a final termination event to close the frontend connection cleanly
            final_metadata = {"event": "done"}
            yield f"data: {json.dumps(final_metadata)}\n\n"

        except Exception as streaming_error:
            # Handle AI failure or client disconnecting mid-stream
            print(f"[-] Streaming interrupted: {streaming_error}")
            
            # Save whatever partial answer was generated before the crash
            if accumulated_answer:
                partial_answer = models.AnswerEntity(
                    qa_pair_id=new_qa_pair.id,
                    content=accumulated_answer + "\n[System: Generation interrupted]"
                )
                db_session.add(partial_answer)
                await db_session.commit()
                
            yield f"data: {json.dumps({'event': 'error', 'detail': 'Generation failed'})}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@router.post("/{qa_pair_id}/retry", response_model=schemas.QAPairResponse)
async def retry_message(
    qa_pair_id: int,
    db_session: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """
    Regenerates the answer for a specific message.
    Truncates the chat history from this point onward and creates a new QA pair.
    """
    # Fetch the target QA Pair with its question
    query = select(models.QAPairEntity).options(
        selectinload(models.QAPairEntity.chat),
        selectinload(models.QAPairEntity.question)
    ).where(
        models.QAPairEntity.id == qa_pair_id,
        models.QAPairEntity.deleted_at.is_(None)
    )
    target_qa = (await db_session.execute(query)).scalars().first()
    
    if not target_qa or target_qa.chat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Message not found.")
    
    # Extract the old question content before we hide it
    original_question_text = target_qa.question.content

    # Soft delete this QA Pair and everything that came after it
    await soft_delete_subsequent_history(
        db_session=db_session,
        chat_id=target_qa.chat_id,
        target_timestamp=target_qa.created_at
    )
    
    # Reuse the /send logic by calling the endpoint function directly
    retry_payload = schemas.MessageSendRequest(
        chat_id=target_qa.chat_id, 
        content=original_question_text
    )

    return await send_message_stream(payload=retry_payload, db_session=db_session, current_user=current_user)


@router.put("/{qa_pair_id}/edit", response_model=schemas.QAPairResponse)
async def edit_message(
    qa_pair_id: int,
    payload: schemas.MessageEditRequest,
    db_session: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """
    Edits a specific question.
    Truncates the chat history from this point onward and generates a new answer.
    """
    # Fetch the target QA Pair
    query = select(models.QAPairEntity).options(
        selectinload(models.QAPairEntity.chat)
    ).where(
        models.QAPairEntity.id == qa_pair_id,
        models.QAPairEntity.deleted_at.is_(None)
    )
    target_qa = (await db_session.execute(query)).scalars().first()

    if not target_qa or target_qa.chat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Message not found.")

    # Soft delete this QA Pair and everything that came after it
    await soft_delete_subsequent_history(
        db_session=db_session,
        chat_id=target_qa.chat_id,
        target_timestamp=target_qa.created_at
    )
    
    # Reuse the /send logic by calling the endpoint function directly
    edit_payload = schemas.MessageSendRequest(
        chat_id=target_qa.chat_id, 
        content=payload.new_content
    )
    
    return await send_message_stream(payload=edit_payload, db_session=db_session, current_user=current_user)