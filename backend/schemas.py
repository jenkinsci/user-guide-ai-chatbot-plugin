from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List


# ==========================================
# CONTEXT SCHEMAS
# ==========================================
class UploadContext(BaseModel):
    pass


class ContextResponse(BaseModel):
    pass


# ==========================================
# CHAT SCHEMAS
# ==========================================

# Data required to create a new chat
class ChatCreateRequest(BaseModel):
    title: str

class ChatTitleUpdateRequest(BaseModel):
    new_title: str

 

class ChatResponse(BaseModel):
    id: int
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime

    # Enables automatic mapping from SQLAlchemy ORM objects
    model_config = ConfigDict(from_attributes=True)


class PaginatedChatResponse(BaseModel):
    items: List[ChatResponse] = Field(default_factory=list)
    total_items: int
    limit: int
    offset: int


# ==========================================
# MESSAGE SCHEMAS
# ==========================================


class MessageSendRequest(BaseModel):
    chat_id: int
    content: str


class MessageEditRequest(BaseModel):
    new_content: str


class QuestionResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AnswerResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class QAPairResponse(BaseModel):
    id: int
    chat_id: int
    created_at: datetime
    question: QuestionResponse
    answer: AnswerResponse
    model_config = ConfigDict(from_attributes=True)


class PaginatedQAResponse(BaseModel):
    items: List[QAPairResponse] = Field(default_factory=list)
    total_items: int
    limit: int
    offset: int
