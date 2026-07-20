from fastapi import Depends, HTTPException, status, Request
from typing import Optional
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# User role constants
ROLE_ADMIN = "admin"
ROLE_ORG_MANAGER = "org_manager"
ROLE_AUDITOR = "auditor"
ROLE_USER = "user"
ROLE_MEMORY_WRITER = "memory_writer"
ROLE_MEMORY_READER = "memory_reader"

async def get_current_user(request: Request):
    """Get the current authenticated user."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return user

async def get_current_user_id(request: Request):
    """Get the current authenticated user ID."""
    user = await get_current_user(request)
    return user.id

async def get_current_user_role(request: Request):
    """Get the current user's role."""
    user = await get_current_user(request)
    return user.role

async def require_admin(request: Request):
    """Require admin role."""
    user = await get_current_user(request)
    if user.role != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user

async def require_org_manage(request: Request):
    """Require organization management privileges."""
    user = await get_current_user(request)
    if user.role not in [ROLE_ADMIN, ROLE_ORG_MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization management privileges required"
        )
    return user

async def require_audit_read(request: Request):
    """Require audit read privileges."""
    user = await get_current_user(request)
    if user.role not in [ROLE_ADMIN, ROLE_AUDITOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Audit read privileges required"
        )
    return user

async def require_memory_write(request: Request):
    """Require memory write permissions."""
    user = await get_current_user(request)
    if user.role not in [ROLE_ADMIN, ROLE_USER, ROLE_MEMORY_WRITER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Memory write privileges required"
        )
    return user

async def require_memory_read(request: Request):
    """Require memory read permissions."""
    user = await get_current_user(request)
    if user.role not in [ROLE_ADMIN, ROLE_USER, ROLE_MEMORY_READER, ROLE_MEMORY_WRITER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Memory read privileges required"
        )
    return user

async def require_enterprise_access(request: Request):
    """Require enterprise access."""
    user = await get_current_user(request)
    if user.role not in [ROLE_ADMIN, ROLE_ORG_MANAGER, "enterprise_user"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Enterprise access required"
        )
    return user

@asynccontextmanager
async def get_db():
    """Database session dependency."""
    from app.db.session import SessionLocal
    async with SessionLocal() as session:
        yield session
