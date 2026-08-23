"""
Chat Sessions Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionUpdate
)

router = APIRouter(prefix="/api/v1/chat/sessions", tags=["chat-sessions"])

@router.get("/")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all chat sessions for the current user"""
    try:
        stmt = select(ChatSession).where(ChatSession.user_id == current_user.id).order_by(ChatSession.pinned.desc(), ChatSession.updated_at.desc())
        result = await db.execute(stmt)
        sessions = result.scalars().all()
        
        session_list = []
        for session in sessions:
            count_stmt = select(func.count()).select_from(ChatMessage).where(ChatMessage.session_id == session.id)
            count_result = await db.execute(count_stmt)
            message_count = count_result.scalar() or 0
            
            updated_at = session.updated_at or session.created_at
            
            session_list.append({
                "id": session.id,
                "title": session.title,
                "user_id": session.user_id,
                "pinned": session.pinned or 0,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "updated_at": updated_at.isoformat() if updated_at else None,
                "message_count": message_count
            })
        
        return session_list
    except Exception as e:
        print(f"❌ Error listing sessions: {e}")
        import traceback
        traceback.print_exc()
        return []

@router.post("/")
async def create_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session"""
    try:
        now = datetime.utcnow()
        new_session = ChatSession(
            title=session_data.title or "New Chat",
            user_id=current_user.id,
            pinned=0,
            created_at=now,
            updated_at=now
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        
        return {
            "id": new_session.id,
            "title": new_session.title,
            "user_id": new_session.user_id,
            "pinned": new_session.pinned or 0,
            "created_at": new_session.created_at.isoformat() if new_session.created_at else None,
            "updated_at": new_session.updated_at.isoformat() if new_session.updated_at else None,
            "message_count": 0
        }
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.get("/{session_id}/messages")
async def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all messages for a session"""
    try:
        stmt = select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
        result = await db.execute(stmt)
        messages = result.scalars().all()
        
        return {
            "session_id": session_id,
            "title": session.title,
            "messages": [{
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "provider": getattr(m, 'provider', None),
                "created_at": m.created_at.isoformat() if m.created_at else None
            } for m in messages]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting messages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")

@router.patch("/{session_id}")
async def update_session(
    session_id: int,
    session_data: ChatSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a chat session title"""
    try:
        stmt = select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.title = session_data.title
        session.updated_at = datetime.utcnow()
        await db.commit()
        
        return {"status": "success", "message": "Session updated"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update session")

@router.delete("/{session_id}")
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session"""
    try:
        stmt = select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        await db.delete(session)
        await db.commit()
        
        return {"status": "success", "message": "Session deleted"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete session")

@router.patch("/{session_id}/pin")
async def pin_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Pin a session"""
    try:
        stmt = select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.pinned = 1
        session.updated_at = datetime.utcnow()
        await db.commit()
        
        return {"status": "success", "message": "Session pinned"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to pin session")

@router.patch("/{session_id}/unpin")
async def unpin_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unpin a session"""
    try:
        stmt = select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.pinned = 0
        session.updated_at = datetime.utcnow()
        await db.commit()
        
        return {"status": "success", "message": "Session unpinned"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to unpin session")
