"""
Chat Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Chat"

class ChatSessionUpdate(BaseModel):
    title: str

class ChatSessionResponse(BaseModel):
    id: int
    title: str
    user_id: int
    pinned: Optional[int] = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: Optional[int] = 0

class ChatMessageCreate(BaseModel):
    session_id: int
    role: str
    content: str
    provider: Optional[str] = None

class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    provider: Optional[str] = None
    created_at: datetime

class ChatRequest(BaseModel):
    query: str
    provider: Optional[str] = "groq"
    session_id: Optional[int] = None
    track_thoughts: Optional[bool] = True

class ChatResponse(BaseModel):
    response: str
    session_id: int
    provider: str
    thought_process: Optional[List[dict]] = []

class ThoughtStep(BaseModel):
    step: int
    label: str
    description: Optional[str] = ""
    status: str
    duration: Optional[float] = 0
    data: Optional[dict] = {}
