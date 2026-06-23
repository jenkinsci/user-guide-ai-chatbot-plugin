from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import models
import schemas
from database import get_database_session
from routers.auth import get_current_user, User 

router = APIRouter(prefix="/chats", tags=["Chats Management"])

# ==========================================
# 1. CREATE ENDPOINT (POST)
# ==========================================
@router.post("/", response_model=schemas.ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_new_chat(
    chat_data: schemas.ChatCreateRequest,
    db_session: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user)  
):
    """
    Creates a new chat session linked to the authenticated user.
    """
    new_chat_record = models.ChatEntity(
        title=chat_data.title,
        user_id=current_user.id
    )

    db_session.add(new_chat_record)
    await db_session.commit()

    await db_session.refresh(new_chat_record)

    return new_chat_record

# ==========================================
# 2. READ ENDPOINT (GET - List)
# ==========================================
@router.get("/", response_model=List[schemas.ChatResponse])
async def get_my_chats(
    db_session: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all active chats belonging to the authenticated user.
    Strictly filters out soft-deleted chats.
    """
    query = select(models.ChatEntity).where(
        models.ChatEntity.user_id == current_user.id,
        models.ChatEntity.deleted_at.is_(None)
    ).order_by(models.ChatEntity.created_at.desc())

    execution_result = await db_session.execute(query)
    
    # scalars().all() extracts the actual ORM objects from the result set
    user_chats = execution_result.scalars().all()

    return user_chats