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
        return env

    async def get_environment(self, env_id: str) -> Optional[Environment]:
        return self._environments.get(env_id)

    async def list_environments(self) -> List[Environment]:
        return list(self._environments.values())

# Singleton instance for simple access in this prototype phase
environment_service = EnvironmentService()
