"""
User Connections API - Connect, collaborate, and share intelligence
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.controlled_user import UserConnection, ConnectionStatus
from app.models.decision_trace import DecisionTrace

router = APIRouter(prefix="/api/v1/connections", tags=["connections"])


class ConnectionRequest(BaseModel):
    target_user_id: str
    message: str = ""


class ConnectionResponse(BaseModel):
    id: str
    user_id: str
    username: str
    role: str
    connected_at: str
    message: Optional[str] = None


@router.post("/request")
async def request_connection(
    request: ConnectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Request to connect with another user."""
    # Check if target exists
    result = await db.execute(select(User).where(User.id == request.target_user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot connect to yourself")
    
    # Check if already connected
    result = await db.execute(
        select(UserConnection)
        .where(
            or_(
                and_(UserConnection.user_id == current_user.id, UserConnection.connected_user_id == request.target_user_id),
                and_(UserConnection.user_id == request.target_user_id, UserConnection.connected_user_id == current_user.id)
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        if existing.status == ConnectionStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Already connected")
        elif existing.status == ConnectionStatus.PENDING:
            raise HTTPException(status_code=400, detail="Connection request already pending")
    
    connection = UserConnection(
        user_id=current_user.id,
        connected_user_id=request.target_user_id,
        status=ConnectionStatus.PENDING,
        message=request.message
    )
    db.add(connection)
    await db.commit()
    await db.refresh(connection)
    
    return {
        "status": "success",
        "message": f"Connection request sent to {target.username}",
        "connection_id": str(connection.id)
    }


@router.get("/pending")
async def get_pending_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get pending connection requests."""
    result = await db.execute(
        select(UserConnection, User)
        .join(User, User.id == UserConnection.user_id)
        .where(UserConnection.connected_user_id == current_user.id)
        .where(UserConnection.status == ConnectionStatus.PENDING)
        .order_by(desc(UserConnection.created_at))
    )
    
    connections = []
    for connection, user in result:
        connections.append({
            "id": str(connection.id),
            "user_id": str(user.id),
            "username": user.username,
            "email": user.email,
            "message": connection.message,
            "created_at": connection.created_at.isoformat() if connection.created_at else None
        })
    
    return {"pending": connections, "total": len(connections)}


@router.post("/{connection_id}/accept")
async def accept_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Accept a connection request."""
    result = await db.execute(
        select(UserConnection)
        .where(UserConnection.id == connection_id)
        .where(UserConnection.connected_user_id == current_user.id)
        .where(UserConnection.status == ConnectionStatus.PENDING)
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection request not found")
    
    connection.status = ConnectionStatus.ACTIVE
    connection.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"status": "success", "message": "Connection accepted"}


@router.post("/{connection_id}/reject")
async def reject_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject a connection request."""
    result = await db.execute(
        select(UserConnection)
        .where(UserConnection.id == connection_id)
        .where(UserConnection.connected_user_id == current_user.id)
        .where(UserConnection.status == ConnectionStatus.PENDING)
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection request not found")
    
    await db.delete(connection)
    await db.commit()
    
    return {"status": "success", "message": "Connection rejected"}


@router.get("/")
async def get_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all active connections."""
    result = await db.execute(
        select(UserConnection, User)
        .join(User, User.id == UserConnection.user_id)
        .where(
            or_(
                UserConnection.user_id == current_user.id,
                UserConnection.connected_user_id == current_user.id
            )
        )
        .where(UserConnection.status == ConnectionStatus.ACTIVE)
    )
    
    connections = []
    for connection, user in result:
        # Determine the other user
        other_user_id = connection.connected_user_id if connection.user_id == current_user.id else connection.user_id
        other_user = await db.get(User, other_user_id)
        if other_user:
            connections.append({
                "id": str(connection.id),
                "user_id": str(other_user.id),
                "username": other_user.username,
                "role": other_user.role,
                "connected_at": connection.updated_at.isoformat() if connection.updated_at else None
            })
    
    return {"connections": connections, "total": len(connections)}


@router.post("/{connection_id}/share-pattern")
async def share_pattern(
    connection_id: str,
    pattern_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Share a pattern with a connected user."""
    # Verify connection exists and is active
    result = await db.execute(
        select(UserConnection)
        .where(UserConnection.id == connection_id)
        .where(
            or_(
                UserConnection.user_id == current_user.id,
                UserConnection.connected_user_id == current_user.id
            )
        )
        .where(UserConnection.status == ConnectionStatus.ACTIVE)
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Get the pattern
    result = await db.execute(
        select(DecisionTrace)
        .where(DecisionTrace.id == pattern_id)
        .where(DecisionTrace.user_id == current_user.id)
    )
    pattern = result.scalar_one_or_none()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    # Create a shared copy for the connected user
    shared_pattern = DecisionTrace(
        session_id=pattern.session_id,
        step=pattern.step,
        data=pattern.data,
        confidence_score=pattern.confidence_score,
        is_crystallized=pattern.is_crystallized,
        query=f"[Shared from {current_user.username}] {pattern.query}" if pattern.query else None,
        pack_name=pattern.pack_name,
        user_id=connection.connected_user_id if connection.user_id == current_user.id else connection.user_id
    )
    db.add(shared_pattern)
    await db.commit()
    
    return {
        "status": "success",
        "message": "Pattern shared successfully",
        "shared_pattern_id": str(shared_pattern.id)
    }
