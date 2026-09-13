from typing import Dict, Optional, List
from datetime import datetime
import uuid
from app.api.v2.models.environment import Environment, EnvironmentStatus

class EnvironmentService:
    def __init__(self):
        print("DEBUG: EnvironmentService __init__ called")
        self._environments: Dict[str, Environment] = {
            "env-default-001": Environment(
                id="env-default-001",
                type="standard",
                name="Default Sovereign Environment",
                owner_principal_id="1",
                status=EnvironmentStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        }

    async def seed_admin_membership(self):
        print("DEBUG: seed_admin_membership started")
        from app.api.v2.services.membership_service import membership_service
        from app.api.v2.models.principal import Principal
        now = datetime.utcnow()
        admin_principal = Principal(id="1", type="person", name="admin", created_at=now, updated_at=now)
        env = self._environments["env-default-001"]
        await membership_service.add_member(env, admin_principal, "owner")
        print(f"DEBUG: Seeded admin membership for principal: {admin_principal.id}")

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

    def reset(self):
        """Reset environments for testing."""
        self._environments = {
            "env-default-001": Environment(
                id="env-default-001",
                type="standard",
                name="Default Sovereign Environment",
                owner_principal_id="1",
                status=EnvironmentStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        }

# Singleton instance for simple access in this prototype phase
environment_service = EnvironmentService()
