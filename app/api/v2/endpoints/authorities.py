from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from app.api.v2.models.authority import AuthorityGrant
from app.api.v2.models.principal import Principal
from app.api.v2.models.environment import Environment
from app.api.v2.services.authority_service import AuthorityService, authority_service
from app.api.v2.services.environment_service import environment_service
from app.api.v2.dependencies import require_authority, get_authority_service, get_environment_service
from pydantic import BaseModel
from datetime import datetime
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/{env_id}/authorities", tags=["v2-authority"])

class AuthorityCreate(BaseModel):
    principal_id: str
    capability: str
    scope: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None

async def require_manage_authorities(
    env_id: str, 
    current_user: User = Depends(get_current_user),
    auth_service = Depends(get_authority_service),
    env_service = Depends(get_environment_service)
):
    return await require_authority(env_id, "manage_authorities", current_user, auth_service, env_service)

@router.post("/", response_model=AuthorityGrant)
async def grant_authority(
    auth_in: AuthorityCreate,
    env: Environment = Depends(require_manage_authorities)
):
    """Grant authority in the environment (Authority check)."""
    # Prototype: dummy principal
    principal = Principal(id=auth_in.principal_id, type="person", name="User", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    
    return await authority_service.grant_authority(
        principal, env, auth_in.capability, auth_in.scope, auth_in.conditions
    )
