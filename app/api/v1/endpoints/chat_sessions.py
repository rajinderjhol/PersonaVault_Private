"""
Chat Session Management Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.core.dependencies import get_current_user_id
from app.models import ChatSession, ChatMessage

router = APIRouter(prefix="/api/v1/chat", tags=["chat-sessions"])

class SessionCreate(BaseModel):
    title: Optional[str] = "New Chat"

class SessionUpdate(BaseModel):
    title: str

@router.post("/sessions")
async def create_session(
    data: SessionCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session."""
    try:
        session = ChatSession(
            user_id=user_id,
            title=data.title or "New Chat",
            created_at=datetime.utcnow()
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return {"id": session.id, "title": session.title}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.get("/sessions")
async def list_sessions(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List all chat sessions for the user."""
    try:
        # Get sessions with message count
        stmt = select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc())
        result = await db.execute(stmt)
        sessions = result.scalars().all()
        
        # Get message counts for each session
        session_list = []
        for s in sessions:
            msg_count_stmt = select(func.count(ChatMessage.id)).where(ChatMessage.session_id == s.id)
            msg_count = await db.execute(msg_count_stmt)
            session_list.append({
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.created_at.isoformat(),
                "message_count": msg_count.scalar_one() or 0
            })
        
        return session_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

@router.patch("/sessions/{session_id}")
async def update_session(
    session_id: int,
    data: SessionUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update a chat session title."""
    try:
        stmt = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        )
        result = await db.execute(stmt)
        session = result.scalars().first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session.title = data.title
        await db.commit()
        return {"id": session.id, "title": session.title}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session and all its messages."""
    try:
        # Delete messages first
        stmt = delete(ChatMessage).where(ChatMessage.session_id == session_id)
        await db.execute(stmt)
        
        # Delete session
        stmt = delete(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        )
        result = await db.execute(stmt)
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"status": "deleted"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get all messages for a session."""
    try:
        # Verify session belongs to user
        stmt = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        )
        result = await db.execute(stmt)
        session = result.scalars().first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get messages
        stmt = select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp.asc())
        result = await db.execute(stmt)
        messages = result.scalars().all()
        
        return {
            "id": session.id,
            "title": session.title,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in messages
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")
