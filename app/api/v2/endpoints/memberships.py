from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.api.v2.models.membership import Membership
from app.api.v2.models.principal import Principal
from app.api.v2.services.membership_service import MembershipService
from app.api.v2.services.environment_service import environment_service
from pydantic import BaseModel

router = APIRouter(prefix="/v2/environments/{env_id}/members", tags=["v2-membership"])

# Prototype dependency injection
membership_service = MembershipService(session_factory=None)

class MembershipCreate(BaseModel):
    principal_id: str
    role: str
    permissions: Optional[List[str]] = None

@router.post("/", response_model=Membership)
async def add_member(env_id: str, mem_in: MembershipCreate):
    """Add a member to the environment."""
    env = await environment_service.get_environment(env_id)
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
        
    # Prototype: create a dummy principal for the ID
    from datetime import datetime
    principal = Principal(id=mem_in.principal_id, type="person", name="User", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    
    return await membership_service.add_member(env, principal, mem_in.role, mem_in.permissions)

@router.get("/", response_model=List[Membership])
async def get_members(env_id: str):
    """List members of the environment."""
    env = await environment_service.get_environment(env_id)
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    return await membership_service.get_members(env)
