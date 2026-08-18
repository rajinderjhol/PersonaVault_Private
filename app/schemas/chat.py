"""
Chat Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ============ CHAT SESSION SCHEMAS ============

class ChatSessionCreate(BaseModel):
    """Schema for creating a new chat session"""
    title: Optional[str] = "New Chat"

class ChatSessionUpdate(BaseModel):
    """Schema for updating a chat session"""
    title: str

class ChatSessionResponse(BaseModel):
    """Schema for chat session response"""
    id: int
    title: str
    user_id: int
    pinned: Optional[int] = 0
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0

# ============ CHAT MESSAGE SCHEMAS ============

class ChatMessageCreate(BaseModel):
    """Schema for creating a new chat message"""
    session_id: int
    role: str  # 'user' or 'assistant'
    content: str
    provider: Optional[str] = None

class ChatMessageResponse(BaseModel):
    """Schema for chat message response"""
    id: int
    session_id: int
    role: str
    content: str
    provider: Optional[str] = None
    created_at: datetime

# ============ CHAT REQUEST/RESPONSE SCHEMAS ============

class ChatRequest(BaseModel):
    """Schema for chat request"""
    query: str
    provider: Optional[str] = "groq"
    session_id: Optional[int] = None
    track_thoughts: Optional[bool] = True

class ChatResponse(BaseModel):
    """Schema for chat response"""
    response: str
    session_id: int
    provider: str
    thought_process: Optional[List[dict]] = []

# ============ THOUGHT PROCESS SCHEMAS ============

class ThoughtStep(BaseModel):
    """Schema for individual thought process step"""
    step: int
    label: str
    description: Optional[str] = ""
    status: str  # 'active', 'complete', 'error'
    duration: Optional[float] = 0
    data: Optional[dict] = {}
