from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.api.v2.models.membership import Membership
from app.api.v2.models.principal import Principal
from app.api.v2.models.environment import Environment
from app.api.v2.services.membership_service import MembershipService, membership_service
from app.api.v2.services.environment_service import environment_service
from app.api.v2.dependencies import require_authority, require_membership, get_authority_service, get_environment_service
from pydantic import BaseModel
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/{env_id}/members", tags=["v2-membership"])

class MembershipCreate(BaseModel):
    principal_id: str
    role: str
    permissions: Optional[List[str]] = None

async def require_manage_membership(
    env_id: str, 
    current_user: User = Depends(get_current_user),
    auth_service = Depends(get_authority_service),
    env_service = Depends(get_environment_service)
):
    return await require_authority(env_id, "manage_membership", current_user, auth_service, env_service)

@router.post("/", response_model=Membership)
async def add_member(
    mem_in: MembershipCreate,
    env: Environment = Depends(require_manage_membership)
):
    """Add a member to the environment (Authority check)."""
    # Prototype: create a dummy principal for the ID
    from datetime import datetime
    principal = Principal(id=mem_in.principal_id, type="person", name="User", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    
    return await membership_service.add_member(env, principal, mem_in.role, mem_in.permissions)

@router.get("/", response_model=List[Membership])
async def get_members(
    env: Environment = Depends(require_membership)
):
    """List members of the environment (Membership check)."""
    return await membership_service.get_members(env)
