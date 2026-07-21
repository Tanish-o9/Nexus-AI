from pydantic import BaseModel, Field
from typing import Literal
from uuid import UUID


class ChatMessage(BaseModel):
    role: Literal['user', 'assistant', 'system']
    content: str


class Citation(BaseModel):
    id: str
    title: str
    source: str
    excerpt: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: str = Field(..., description='Unique conversation session ID')
    user_id: str = Field(..., description='Authenticated user ID from Django')
    org_id: str | None = None
    project_id: str | None = None
    file_ref: str | None = None
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class ChatResponse(BaseModel):
    session_id: str
    content: str
    citations: list[Citation] = []
    agent_trace: list[str] = []  # which agents ran, for debugging


class StreamChunk(BaseModel):
    type: Literal['token', 'citation', 'done', 'error']
    data: str
