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


class CommitInfo(BaseModel):
    commit_id: Optional[str] = Field(default=None, alias="commitId")
    author: Optional[str] = None
    message: Optional[str] = None


class TestResults(BaseModel):
    total: Optional[int] = None
    failed: Optional[int] = None
    skipped: Optional[int] = None


class BuildDetails(BaseModel):
    number: Optional[int] = None
    result: Optional[BuildResult] = None
    duration: Optional[int] = None
    timestamp: Optional[int] = None

    causes: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None
    test_results: Optional[TestResults] = Field(default=None, alias="testResults")
    built_on_node: Optional[str] = Field(default=None, alias="builtOnNode")

    changes: Optional[List[CommitInfo]] = None

    console_log_tail: Optional[str] = Field(default=None, alias="consoleLogTail")
    previous_build: Optional["BuildDetails"] = Field(
        default=None, alias="previousBuild"
    )


class JobDetails(BaseModel):
    full_name: Optional[str] = Field(default=None, alias="fullName")
    job_type: Optional[str] = Field(default=None, alias="jobType")

    # New general metadata
    url: Optional[str] = Field(default=None)
    is_buildable: Optional[bool] = Field(default=None, alias="isBuildable")
    in_queue: Optional[bool] = Field(default=None, alias="inQueue")
    health_score: Optional[int] = Field(default=None, alias="healthScore")
    description: Optional[str] = Field(default=None)

    config_xml: Optional[str] = Field(default=None, alias="configXml")
    is_pipeline: Optional[bool] = Field(default=None, alias="isPipeline")

    # Pipeline specific
    concurrent_build: Optional[bool] = Field(default=None, alias="concurrentBuild")

    # Classic project specific
    upstream_projects: Optional[List[str]] = Field(
        default=None, alias="upstreamProjects"
    )
    downstream_projects: Optional[List[str]] = Field(
        default=None, alias="downstreamProjects"
    )

    # Keep the workspace tree if you are still extracting it
    workspace_tree: Optional[List[str]] = Field(default=None, alias="workspaceTree")


class SystemInfo(BaseModel):
    os_name: Optional[str] = Field(default=None, alias="osName")
    os_arch: Optional[str] = Field(default=None, alias="osArch")
    os_version: Optional[str] = Field(default=None, alias="osVersion")
    java_version: Optional[str] = Field(default=None, alias="javaVersion")
    available_processors: Optional[int] = Field(
        default=None, alias="availableProcessors"
    )
    free_memory_mb: Optional[int] = Field(default=None, alias="freeMemoryMB")
    total_memory_mb: Optional[int] = Field(default=None, alias="totalMemoryMB")
    max_memory_mb: Optional[int] = Field(default=None, alias="maxMemoryMB")


class MasterNode(BaseModel):
    executors: Optional[int] = None
    is_online: Optional[bool] = Field(default=None, alias="isOnline")
    system_info: Optional[SystemInfo] = Field(default=None, alias="systemInfo")


class AgentStats(BaseModel):
    online_agents: Optional[int] = Field(default=None, alias="onlineAgents")
    offline_agents: Optional[int] = Field(default=None, alias="offlineAgents")


class JenkinsContext(BaseModel):
    current_screen: Optional[str] = Field(default=None, alias="currentScreen")
    jenkins_version: Optional[str] = Field(default=None, alias="jenkinsVersion")
    root_url: Optional[str] = Field(default=None, alias="rootUrl")
    system_message: Optional[str] = Field(default=None, alias="systemMessage")

    active_plugins: Optional[Dict[str, str]] = Field(
        default=None, alias="activePlugins"
    )
    master_node: Optional[MasterNode] = Field(default=None, alias="masterNode")
    agent_stats: Optional[AgentStats] = Field(default=None, alias="agentStats")

    job_details: Optional[JobDetails] = Field(default=None, alias="jobDetails")
    build_details: Optional[BuildDetails] = Field(default=None, alias="buildDetails")

    context_parsing_error: Optional[str] = Field(
        default=None, alias="contextParsingError"
    )


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
