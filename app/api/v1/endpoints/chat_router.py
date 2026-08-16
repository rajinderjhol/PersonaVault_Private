from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from datetime import datetime

from app.db.session import get_db
from app.models.chat import ChatSession, ChatMessage
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

@router.post("/sessions")
async def create_session(
    title: str = "New Chat",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = ChatSession(user_id=current_user.id, title=title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

@router.get("/sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(ChatSession).where(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    stmt = select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
    session = (await db.execute(stmt)).scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/sessions/{session_id}/messages")
async def add_message(
    session_id: int,
    role: str,
    content: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    stmt = select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
    session = (await db.execute(stmt)).scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    message = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message
