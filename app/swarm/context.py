from typing import Optional, Dict, Any, List
from app.services.memory_service import MemoryService
from app.api.v2.services.authority_service import AuthorityService
from app.api.v2.services.crystallization_service import CrystallizationService

class AgentEnvironmentContext:
    def __init__(self, environment_id: str, memory_service: MemoryService, authority_service: AuthorityService, crystallization_service: CrystallizationService):
        self.environment_id = environment_id
        self.memory_service = memory_service
        self.authority_service = authority_service
        self.crystallization_service = crystallization_service

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

    async def learn_pattern(self, pattern_data: Dict[str, Any]) -> str:
        """Crystallize a new pattern from a learning experience."""
        # Need to resolve environment object
        from app.api.v2.services.environment_service import environment_service
        env = await environment_service.get_environment(self.environment_id)
        return await self.crystallization_service.crystallize_pattern(
            environment=env,
            pattern_data=pattern_data
        )

    async def recall_patterns(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve crystallized patterns relevant to the query."""
        from app.api.v2.services.environment_service import environment_service
        env = await environment_service.get_environment(self.environment_id)
        return await self.crystallization_service.retrieve_crystallized_patterns(
            environment=env,
            query=query
        )
