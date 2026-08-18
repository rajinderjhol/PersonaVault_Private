"""
Chat Sessions Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionResponse,
    ChatMessageResponse
)

# Use prefix without trailing slash
router = APIRouter(
    prefix="/api/v1/chat",
    tags=["chat-sessions"]
)

# ============ MODELS ============
class SessionPinUpdate(BaseModel):
    pinned: bool

# ============ ENDPOINTS ============

@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all chat sessions for the current user"""
    try:
        from sqlalchemy import select
        stmt = select(ChatSession).where(ChatSession.user_id == current_user.id).order_by(ChatSession.pinned.desc(), ChatSession.created_at.desc())
        result = await db.execute(stmt)
        sessions = result.scalars().all()
        
        session_list = []
        for session in sessions:
            from sqlalchemy import func, select
            count_stmt = select(func.count()).select_from(ChatMessage).where(ChatMessage.session_id == session.id)
            count_result = await db.execute(count_stmt)
            message_count = count_result.scalar() or 0
            
            session_list.append({
                "id": session.id,
                "title": session.title,
                "user_id": session.user_id,
                "pinned": session.pinned or 0,
                "created_at": session.created_at,
                "updated_at": session.updated_at or session.created_at,
                "message_count": message_count
            })
        
        return session_list
    except Exception as e:
        print(f"❌ Error listing sessions: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")

@router.post("/sessions")
async def create_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session"""
    try:
        print(f"Creating session for user {current_user.id} with title: {session_data.title}")
        
        new_session = ChatSession(
            title=session_data.title or "New Chat",
            user_id=current_user.id,
            pinned=0,
            created_at=datetime.utcnow()
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        
        print(f"✅ Session created with ID: {new_session.id}")
        
        return {
            "id": new_session.id,
            "title": new_session.title,
            "user_id": new_session.user_id,
            "pinned": new_session.pinned or 0,
            "created_at": new_session.created_at,
            "updated_at": new_session.updated_at or new_session.created_at,
            "message_count": 0
        }
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        import traceback
        traceback.print_exc()
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all messages for a session"""
    try:
        from sqlalchemy import select
        stmt = select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.asc())
        result = await db.execute(stmt)
        messages = result.scalars().all()
        
        return {
            "session_id": session_id,
            "title": session.title,
            "messages": [{
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp
            } for m in messages]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get messages")

@router.patch("/sessions/{session_id}")
async def update_session(
    session_id: int,
    session_data: ChatSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a chat session title"""
    try:
        from sqlalchemy import select
        stmt = select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.title = session_data.title
        await db.commit()
        
        return {"status": "success", "message": "Session updated"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating session: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update session")

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session"""
    try:
        from sqlalchemy import select
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
        print(f"Error deleting session: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete session")

@router.patch("/sessions/{session_id}/pin")
async def pin_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Pin a session to the top of the list"""
    try:
        from sqlalchemy import select
        stmt = select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.pinned = 1
        await db.commit()
        
        return {"status": "success", "message": "Session pinned"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error pinning session: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to pin session")

@router.patch("/sessions/{session_id}/unpin")
async def unpin_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unpin a session"""
    try:
        from sqlalchemy import select
        stmt = select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.pinned = 0
        await db.commit()
        
        return {"status": "success", "message": "Session unpinned"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error unpinning session: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to unpin session")