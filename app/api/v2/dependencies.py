from fastapi import Depends, HTTPException, status
from typing import Optional
from app.api.v2.models.environment import Environment
from app.api.v2.models.principal import Principal
from app.api.v2.services.authority_service import AuthorityService, authority_service
from app.api.v2.services.environment_service import environment_service, EnvironmentService
from app.api.v2.services.membership_service import MembershipService, membership_service
from app.core.dependencies import get_current_user
from app.models.user import User
from datetime import datetime

# Dependencies for V2 services
def get_environment_service() -> 'EnvironmentService':
    return environment_service

def get_authority_service() -> 'AuthorityService':
    return authority_service

def get_membership_service() -> 'MembershipService':
    return membership_service

async def require_authority(
    env_id: str,
    capability: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthorityService = Depends(get_authority_service),
    env_service: EnvironmentService = Depends(get_environment_service)
) -> Environment:
    """
    Dependency that checks if the current user has the required capability
    in the specified environment. Returns the environment if authorized.
    """
    environment = await env_service.get_environment(env_id)
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment not found"
        )
    
    # Simple converter from V1 user to V2 Principal
    principal = Principal(
        id=str(current_user.id),
        type="person",
        name=current_user.username,
        created_at=current_user.last_login or datetime.utcnow(),
        updated_at=current_user.last_login or datetime.utcnow()
    )
    
    # Check authority using the integrated RBAC
    has_auth = await auth_service.check_authority(
        principal=principal,
        environment=environment,
        required_capability=capability,
        path=None # For now, we are checking capability directly, not path-based RBAC
    )
    
    if not has_auth:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have '{capability}' permission in this environment"
        )
    
    return environment

async def require_membership(
    env_id: str,
    current_user: User = Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service),
    env_service: EnvironmentService = Depends(get_environment_service)
) -> Environment:
    """
    Dependency that checks if the current user is a member of the environment.
    Returns the environment if authorized.
    """
    environment = await env_service.get_environment(env_id)
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment not found"
        )
        
    members = await membership_service.get_members(environment)
    member_ids = [m.principal_id for m in members]
    print(f"DEBUG: Membership check for env {environment.id}. Current User ID: {current_user.id}, Members found: {member_ids}")
    
    if not any(m.principal_id == str(current_user.id) for m in members):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User {current_user.id} is not a member of this environment. Members: {member_ids}"
        )
    
    return environment
