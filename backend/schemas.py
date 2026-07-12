from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


# ==========================================
# CONTEXT SCHEMAS
# ==========================================

class BuildResult(str, Enum):
    SUCCESS = "SUCCESS"
    UNSTABLE = "UNSTABLE"
    FAILURE = "FAILURE"
    NOT_BUILT = "NOT_BUILT"
    ABORTED = "ABORTED"
    IN_PROGRESS = "IN_PROGRESS"
    UNKNOWN = "UNKNOWN"

class BuildDetails(BaseModel):
    number: Optional[int] = None
    result: Optional[BuildResult] = None
    duration: Optional[int] = None
    timestamp: Optional[int] = None
    console_log_tail: Optional[str] = Field(default=None, alias="consoleLogTail")
    previous_build: Optional["BuildDetails"] = Field(default=None, alias="previousBuild")

class JobDetails(BaseModel):
    full_name: Optional[str] = Field(default=None, alias="fullName")
    job_type: Optional[str] = Field(default=None, alias="jobType")
    config_xml: Optional[str] = Field(default=None, alias="configXml")
    is_pipeline: Optional[bool] = Field(default=None, alias="isPipeline")

class MasterNode(BaseModel):
    executors: Optional[int] = None
    is_online: Optional[bool] = Field(default=None, alias="isOnline")
    description: Optional[str] = Field(default=None, alias="Description")

class JenkinsContext(BaseModel):
    current_screen: Optional[str] = Field(default=None, alias="currentScreen")
    jenkins_version: Optional[str] = Field(default=None, alias="jenkinsVersion")
    active_plugins: Optional[Dict[str, str]] = Field(default=None, alias="activePlugins")
    master_node: Optional[MasterNode] = Field(default=None, alias="masterNode")
    
    job_details: Optional[JobDetails] = Field(default=None, alias="jobDetails")
    build_details: Optional[BuildDetails] = Field(default=None, alias="buildDetails")
    
    context_parsing_error: Optional[str] = Field(default=None, alias="contextParsingError")

class UploadContext(BaseModel):
    jenkins_context: JenkinsContext = Field(..., alias="jenkinsContext")    

class ContextResponse(BaseModel):
    success: bool
    received_data: JenkinsContext

class LastContextUploadResponse(BaseModel):
    last_upload_at: datetime | None


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
    answer: AnswerResponse | None
    model_config = ConfigDict(from_attributes=True)


class PaginatedQAResponse(BaseModel):
    items: List[QAPairResponse] = Field(default_factory=list)
    total_items: int
    limit: int
    offset: int
