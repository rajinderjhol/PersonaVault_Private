from typing import Optional, List
from app.api.v2.models.membership import Membership
from app.api.v2.models.environment import Environment
from app.api.v2.models.principal import Principal

class MembershipService:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        # In-memory store for prototype
        self._memberships: List[Membership] = []

    async def add_member(
        self,
        environment: Environment,
        principal: Principal,
        role: str,
        permissions: Optional[List[str]] = None
    ) -> Membership:
        """Add a Principal to an Environment with a specific role."""
        import uuid
        from datetime import datetime
        
        membership = Membership(
            id=str(uuid.uuid4()),
            environment_id=environment.id,
            principal_id=principal.id,
            role=role,
            permissions=permissions or [],
            starts_at=datetime.utcnow()
        )
        self._memberships.append(membership)
        return membership

    async def get_members(
        self,
        environment: Environment
    ) -> List[Membership]:
        """Get all members of an Environment."""
        return [m for m in self._memberships if m.environment_id == environment.id]
