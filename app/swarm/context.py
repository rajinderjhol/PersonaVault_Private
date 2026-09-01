from typing import Optional
from app.services.memory_service import MemoryService
from app.api.v2.services.authority_service import AuthorityService

class AgentEnvironmentContext:
    def __init__(self, environment_id: str, memory_service: MemoryService, authority_service: AuthorityService):
        self.environment_id = environment_id
        self.memory_service = memory_service
        self.authority_service = authority_service

    async def retrieve_memory(self, query: str, limit: int = 5):
        return await self.memory_service.search_memories(
            user_id=1, # Simplified for now
            query=query,
            limit=limit,
            environment_id=self.environment_id
        )

    async def check_authority(self, capability: str):
        # Requires Principal resolution which we might need to add later
        return True 
