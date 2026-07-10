"""
Pydantic 数据模型。定义所有 API 的请求体和响应体。
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="用户消息")
    session_id: Optional[str] = Field(None, description="会话 ID，不传则创建新会话")
    mode: Literal["chat", "agent"] = Field("chat", description="对话模式")

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    mode: str

class StreamChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None
    mode: Literal["chat", "agent"] = "chat"


class MemoryItem(BaseModel):
    id: int
    content: str
    category: str
    importance: str
    created_at: str

class MemoryListResponse(BaseModel):
    total: int
    memories: list[MemoryItem]

class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20)
    category: Optional[str] = None


class KnowledgeBaseStatus(BaseModel):
    document_count: int
    chunk_count: int
    documents: list[dict]

class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(3, ge=1, le=10)
    file_filter: Optional[str] = None

class KnowledgeSearchResult(BaseModel):
    file: str
    content: str
    score: float


class ToolInfo(BaseModel):
    name: str
    description: str

class ToolListResponse(BaseModel):
    tools: list[ToolInfo]


class AgentTaskRequest(BaseModel):
    instruction: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None

class AgentTaskStep(BaseModel):
    step: int
    action: str
    result: str
    status: Literal["ok", "error", "stopped"]

class AgentTaskResponse(BaseModel):
    task_id: str
    success: bool
    summary: str
    steps: list[AgentTaskStep]


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "6.0.0"
    tools_count: int
    memory_count: int
