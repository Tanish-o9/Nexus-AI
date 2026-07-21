from pydantic import BaseModel, Field
from datetime import datetime


class MemoryEntry(BaseModel):
    id: str
    agent_id: str
    session_id: str
    user_id: str
    content: str
    embedding: list[float] | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime


class MemoryWriteRequest(BaseModel):
    agent_id: str
    session_id: str
    user_id: str
    content: str
    metadata: dict = Field(default_factory=dict)


class MemoryQueryRequest(BaseModel):
    agent_id: str
    session_id: str
    user_id: str
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
