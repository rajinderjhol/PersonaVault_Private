from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from app.api.v2.models.authority import AuthorityGrant
from app.api.v2.models.principal import Principal
from app.api.v2.services.authority_service import AuthorityService
from app.api.v2.services.environment_service import environment_service
from app.api.v2.endpoints.memberships import membership_service
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/v2/environments/{env_id}/authorities", tags=["v2-authority"])

# Prototype dependency injection
authority_service = AuthorityService(membership_service=membership_service)

class AuthorityCreate(BaseModel):
    principal_id: str
    capability: str
    scope: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None

@router.post("/", response_model=AuthorityGrant)
async def grant_authority(env_id: str, auth_in: AuthorityCreate):
    """Grant authority in the environment."""
    env = await environment_service.get_environment(env_id)
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
        
    # Prototype: dummy principal
    principal = Principal(id=auth_in.principal_id, type="person", name="User", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    
    return await authority_service.grant_authority(
        principal, env, auth_in.capability, auth_in.scope, auth_in.conditions
    )
