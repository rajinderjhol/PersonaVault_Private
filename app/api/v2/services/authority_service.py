from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from app.api.v2.models.authority import AuthorityGrant
from app.api.v2.models.environment import Environment
from app.api.v2.models.principal import Principal
from app.api.v2.services.membership_service import MembershipService
from app.core.permissions import check_permission

class AuthorityService:
    def __init__(self, membership_service: MembershipService):
        self.membership_service = membership_service
        self._grants: Dict[str, AuthorityGrant] = {}

    async def grant_authority(
        self,
        principal: Principal,
        environment: Environment,
        capability: str,
        scope: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None
    ) -> AuthorityGrant:
        """Grant a specific capability to a Principal within an Environment."""
        grant = AuthorityGrant(
            id=str(uuid.uuid4()),
            environment_id=environment.id,
            principal_id=principal.id,
            capability=capability,
            scope=scope,
            conditions=conditions,
            valid_from=datetime.utcnow()
        )
        self._grants[grant.id] = grant
        return grant

    async def check_authority(
        self,
        principal: Principal,
        environment: Environment,
        required_capability: str,
        path: Optional[str] = None
    ) -> bool:
        """Check if a Principal has the required capability in an Environment, integrated with RBAC."""
        # 1. Check membership
        members = await self.membership_service.get_members(environment)
        membership = next((m for m in members if m.principal_id == principal.id), None)
        if not membership:
            return False
        
        # 2. Check existing RBAC system if a path is provided
        if path:
            # Note: This uses the role from the V2 membership
            if not check_permission(membership.role, path):
                return False

        # 3. Check V2 specific authority grants
        return any(
            g.principal_id == principal.id and 
            g.environment_id == environment.id and 
            g.capability == required_capability
            for g in self._grants.values()
        )
