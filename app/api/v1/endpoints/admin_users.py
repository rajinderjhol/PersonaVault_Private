"""
Admin User Management API - User creation, access control, supervision
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

from app.db.session import get_db
from app.core.dependencies import require_admin, get_current_user
from app.models.user import User
from app.models.controlled_user import (
    ControlledUser, AccessLevel, SupervisionMode, 
    ControlledAction, ConnectionStatus, UserConnection
)
from app.services.intelligence_gateway import gateway

router = APIRouter(prefix="/api/v1/admin/users", tags=["admin-users"])
logger = __import__('logging').getLogger(__name__)


class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "analyst"
    access_level: AccessLevel = AccessLevel.STANDARD
    supervision_mode: SupervisionMode = SupervisionMode.NONE
    supervisor_id: Optional[str] = None
    allowed_domains: List[str] = []
    max_confidence_threshold: float = 1.0
    requires_approval: bool = False
    allowed_hours_start: int = 0
    allowed_hours_end: int = 23
    allowed_days: List[int] = [0, 1, 2, 3, 4, 5, 6]
    expires_at: Optional[str] = None
    daily_decision_limit: int = 100
    monthly_decision_limit: int = 1000


class UserUpdateRequest(BaseModel):
    access_level: Optional[AccessLevel] = None
    supervision_mode: Optional[SupervisionMode] = None
    supervisor_id: Optional[str] = None
    allowed_domains: Optional[List[str]] = None
    max_confidence_threshold: Optional[float] = None
    requires_approval: Optional[bool] = None
    allowed_hours_start: Optional[int] = None
    allowed_hours_end: Optional[int] = None
    allowed_days: Optional[List[int]] = None
    expires_at: Optional[str] = None
    daily_decision_limit: Optional[int] = None
    monthly_decision_limit: Optional[int] = None


@router.post("/create")
async def create_controlled_user(
    request: UserCreateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user with controlled access (admin only)."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Check if user already exists
    result = await db.execute(select(User).where(User.username == request.username))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    result = await db.execute(select(User).where(User.email == request.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create user
    user = User(
        username=request.username,
        email=request.email,
        hashed_password=pwd_context.hash(request.password),
        role=request.role,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(user)
    await db.flush()
    
    # Create controlled user settings
    controlled = ControlledUser(
        user_id=user.id,
        access_level=request.access_level,
        supervision_mode=request.supervision_mode,
        supervisor_id=request.supervisor_id,
        allowed_domains=request.allowed_domains,
        max_confidence_threshold=request.max_confidence_threshold,
        requires_approval=request.requires_approval,
        allowed_hours_start=request.allowed_hours_start,
        allowed_hours_end=request.allowed_hours_end,
        allowed_days=request.allowed_days,
        expires_at=datetime.fromisoformat(request.expires_at) if request.expires_at else None,
        daily_decision_limit=request.daily_decision_limit,
        monthly_decision_limit=request.monthly_decision_limit
    )
    db.add(controlled)
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "status": "success",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "access_level": controlled.access_level,
            "supervision_mode": controlled.supervision_mode,
            "supervisor_id": str(controlled.supervisor_id) if controlled.supervisor_id else None,
            "requires_approval": controlled.requires_approval,
            "expires_at": controlled.expires_at.isoformat() if controlled.expires_at else None
        }
    }


@router.get("/list")
async def list_controlled_users(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """List all controlled users (admin only)."""
    result = await db.execute(
        select(User, ControlledUser)
        .join(ControlledUser, User.id == ControlledUser.user_id)
        .offset(skip)
        .limit(limit)
    )
    
    users = []
    for user, controlled in result:
        # Get supervisor username if exists
        supervisor_name = None
        if controlled.supervisor_id:
            sup_result = await db.execute(select(User).where(User.id == controlled.supervisor_id))
            supervisor = sup_result.scalar_one_or_none()
            if supervisor:
                supervisor_name = supervisor.username
        
        users.append({
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "access_level": controlled.access_level,
            "supervision_mode": controlled.supervision_mode,
            "supervisor": supervisor_name,
            "allowed_domains": controlled.allowed_domains,
            "requires_approval": controlled.requires_approval,
            "daily_decision_limit": controlled.daily_decision_limit,
            "expires_at": controlled.expires_at.isoformat() if controlled.expires_at else None,
            "created_at": controlled.created_at.isoformat() if controlled.created_at else None
        })
    
    return {"users": users, "total": len(users)}


@router.get("/{user_id}")
async def get_controlled_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific controlled user (admin only)."""
    result = await db.execute(
        select(User, ControlledUser)
        .join(ControlledUser, User.id == ControlledUser.user_id)
        .where(User.id == user_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    
    user, controlled = row
    
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "access_level": controlled.access_level,
        "supervision_mode": controlled.supervision_mode,
        "supervisor_id": str(controlled.supervisor_id) if controlled.supervisor_id else None,
        "allowed_domains": controlled.allowed_domains,
        "max_confidence_threshold": controlled.max_confidence_threshold,
        "requires_approval": controlled.requires_approval,
        "allowed_hours_start": controlled.allowed_hours_start,
        "allowed_hours_end": controlled.allowed_hours_end,
        "allowed_days": controlled.allowed_days,
        "compliance_flags": controlled.compliance_flags,
        "daily_decision_limit": controlled.daily_decision_limit,
        "monthly_decision_limit": controlled.monthly_decision_limit,
        "expires_at": controlled.expires_at.isoformat() if controlled.expires_at else None,
        "created_at": controlled.created_at.isoformat() if controlled.created_at else None
    }


@router.patch("/{user_id}")
async def update_controlled_user(
    user_id: str,
    request: UserUpdateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a controlled user (admin only)."""
    result = await db.execute(
        select(ControlledUser).where(ControlledUser.user_id == user_id)
    )
    controlled = result.scalar_one_or_none()
    if not controlled:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields if provided
    if request.access_level is not None:
        controlled.access_level = request.access_level
    if request.supervision_mode is not None:
        controlled.supervision_mode = request.supervision_mode
    if request.supervisor_id is not None:
        controlled.supervisor_id = request.supervisor_id
    if request.allowed_domains is not None:
        controlled.allowed_domains = request.allowed_domains
    if request.max_confidence_threshold is not None:
        controlled.max_confidence_threshold = request.max_confidence_threshold
    if request.requires_approval is not None:
        controlled.requires_approval = request.requires_approval
    if request.allowed_hours_start is not None:
        controlled.allowed_hours_start = request.allowed_hours_start
    if request.allowed_hours_end is not None:
        controlled.allowed_hours_end = request.allowed_hours_end
    if request.allowed_days is not None:
        controlled.allowed_days = request.allowed_days
    if request.expires_at is not None:
        controlled.expires_at = datetime.fromisoformat(request.expires_at) if request.expires_at else None
    if request.daily_decision_limit is not None:
        controlled.daily_decision_limit = request.daily_decision_limit
    if request.monthly_decision_limit is not None:
        controlled.monthly_decision_limit = request.monthly_decision_limit
    
    controlled.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(controlled)
    
    return {"status": "success", "message": "User updated"}


@router.patch("/{user_id}/approval")
async def update_approval_requirement(
    user_id: str,
    requires_approval: bool,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update approval requirement for a user (admin only)."""
    result = await db.execute(
        select(ControlledUser).where(ControlledUser.user_id == user_id)
    )
    controlled = result.scalar_one_or_none()
    if not controlled:
        raise HTTPException(status_code=404, detail="User not found")
    
    controlled.requires_approval = requires_approval
    controlled.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"status": "success", "requires_approval": requires_approval}


@router.post("/{user_id}/approve")
async def approve_action(
    user_id: str,
    action_id: str,
    approve: bool,
    reason: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Approve or deny a controlled action (admin only)."""
    result = await db.execute(
        select(ControlledAction).where(ControlledAction.id == action_id)
    )
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    action.status = "approved" if approve else "denied"
    action.approved_by = current_user.id
    action.approved_at = datetime.utcnow()
    action.reason = reason
    
    await db.commit()
    
    return {
        "status": "success",
        "action_id": action_id,
        "approved": approve,
        "reason": reason
    }


@router.get("/actions/pending")
async def get_pending_actions(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """Get all pending approval actions (admin only)."""
    result = await db.execute(
        select(ControlledAction, User)
        .join(User, User.id == ControlledAction.user_id)
        .where(ControlledAction.status == "pending")
        .offset(skip)
        .limit(limit)
    )
    
    actions = []
    for action, user in result:
        actions.append({
            "id": str(action.id),
            "user_id": str(user.id),
            "username": user.username,
            "action_type": action.action_type,
            "request_data": action.request_data,
            "created_at": action.created_at.isoformat() if action.created_at else None
        })
    
    return {"actions": actions, "total": len(actions)}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    # Delete controlled settings first
    controlled_result = await db.execute(
        select(ControlledUser).where(ControlledUser.user_id == user_id)
    )
    controlled = controlled_result.scalar_one_or_none()
    if controlled:
        await db.delete(controlled)
    
    await db.delete(user)
    await db.commit()
    
    return {"status": "success", "message": f"User {user.username} deleted"}
