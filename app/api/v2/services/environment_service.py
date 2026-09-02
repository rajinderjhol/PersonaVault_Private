from typing import Dict, Optional, List
from datetime import datetime
import uuid
from app.api.v2.models.environment import Environment, EnvironmentStatus

class EnvironmentService:
    def __init__(self):
        # In-memory store for development/prototyping
        self._environments: Dict[str, Environment] = {}

    async def create_environment(self, name: str, owner_id: str, type: str = "standard") -> Environment:
        env_id = str(uuid.uuid4())
        now = datetime.utcnow()
        env = Environment(
            id=env_id,
            type=type,
            name=name,
            owner_principal_id=owner_id,
            status=EnvironmentStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        self._environments[env_id] = env
        
        # Auto-add owner as member
        from app.api.v2.services.membership_service import membership_service
        from app.api.v2.services.authority_service import authority_service
        from app.api.v2.models.principal import Principal
        
        owner_principal = Principal(id=owner_id, type="person", name="Owner", created_at=now, updated_at=now)
        await membership_service.add_member(env, owner_principal, "owner")
        
        # Grant administrative authorities
        for capability in ["manage_membership", "manage_authorities", "update_environment", "delete_environment"]:
            await authority_service.grant_authority(owner_principal, env, capability)
        
        return env

    async def get_environment(self, env_id: str) -> Optional[Environment]:
        return self._environments.get(env_id)

    async def list_environments(self) -> List[Environment]:
        return list(self._environments.values())

    async def update_environment(self, env_id: str, updates: dict) -> Environment:
        if env_id not in self._environments:
            raise ValueError("Environment not found")
        
        env = self._environments[env_id]
        # Update attributes
        for key, value in updates.items():
            if hasattr(env, key):
                setattr(env, key, value)
        
        env.updated_at = datetime.utcnow()
        self._environments[env_id] = env
        return env

    async def delete_environment(self, env_id: str) -> bool:
        if env_id in self._environments:
            del self._environments[env_id]
            return True
        return False

# Singleton instance for simple access in this prototype phase
environment_service = EnvironmentService()
