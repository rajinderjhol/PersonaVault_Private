from typing import Optional, Dict, Any, List
from app.api.v2.models.environment import Environment
from app.services.memory_service import MemoryService
from app.api.v2.services.authority_service import AuthorityService
from app.api.v2.services.crystallization_service import CrystallizationService
from app.api.v2.services.prediction_service import PredictionService
from app.api.v2.services.simulation_service import SimulationService

class AgentEnvironmentContext:
    def __init__(
        self,
        environment: Environment,
        memory_service: MemoryService,
        authority_service: AuthorityService,
        crystallization_service: CrystallizationService,
        prediction_service: PredictionService,
        simulation_service: SimulationService
    ):
        self.environment = environment
        self.memory_service = memory_service
        self.authority_service = authority_service
        self.crystallization_service = crystallization_service
        self.prediction_service = prediction_service
        self.simulation_service = simulation_service

    async def retrieve_memory(self, query: str, limit: int = 5):
        return await self.memory_service.search_memories(
            user_id=1, # Simplified for now
            query=query,
            limit=limit,
            environment_id=self.environment.id
        )

    async def check_authority(self, capability: str):
        # We need a way to resolve the current principal.
        # Placeholder for now until context passes Principal object.
        return True 

    async def learn_pattern(self, pattern_data: Dict[str, Any]) -> str:
        """Crystallize a new pattern from a learning experience."""
        return await self.crystallization_service.crystallize_pattern(
            environment=self.environment,
            pattern_data=pattern_data
        )

    async def recall_patterns(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve crystallized patterns relevant to the query."""
        return await self.crystallization_service.retrieve_crystallized_patterns(
            environment=self.environment,
            query=query
        )
