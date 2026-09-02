import time
import json
from typing import Dict, Any, List, Optional
from app.api.v2.models.environment import Environment
from app.services.memory_service import MemoryService
from app.api.v2.services.metrics import track_crystallization

class CrystallizationService:
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service

    async def crystallize_pattern(
        self,
        environment: Environment,
        pattern_data: Dict[str, Any],
        source_decision_id: Optional[str] = None
    ) -> str:
        """
        Store a crystallized pattern within a specific environment.
        Returns the memory ID of the crystallized pattern.
        """
        start_time = time.time()
        
        try:
            # Store the crystallized pattern in memory
            memory_id = await self.memory_service.save_memory(
                user_id=1, # Simplified, should resolve from env context
                memory_type="crystallized_pattern",
                content=pattern_data.get("content", ""),
                tags=pattern_data.get("tags", []),
                title=pattern_data.get("title", "Crystallized Pattern"),
                environment_id=environment.id
            )
            
            # Track success
            duration = time.time() - start_time
            track_crystallization(
                environment_id=environment.id,
                source_type="automated_learning",
                duration=duration,
                status="success"
            )

            return str(memory_id.id)
        except Exception as e:
            # Track failure
            duration = time.time() - start_time
            track_crystallization(
                environment_id=environment.id,
                source_type="automated_learning",
                duration=duration,
                status="failed"
            )
            raise e

    async def retrieve_crystallized_patterns(
        self,
        environment: Environment,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve crystallized patterns scoped to a specific environment.
        """
        memories = await self.memory_service.search_memories(
            user_id=1,
            query=query,
            limit=limit,
            environment_id=environment.id
        )
        
        # Filter by type in Python
        return [m for m in memories if m.get("metadata", {}).get("type") == "crystallized_pattern"]

    async def get_pattern(self, pattern_id: str, environment_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single crystallized pattern by ID, scoped to an environment.
        """
        return await self.memory_service.get_memory(int(pattern_id), environment_id=environment_id)

# Singleton instance
from app.services.memory_service import MemoryService
from app.repositories.sqlalchemy.memory import SQLMemoryRepository
from app.repositories.faiss.vector import FAISSSemanticRepository

# This is a placeholder; in a real app, inject proper session/repo
memory_service = MemoryService(
    memory_repo=SQLMemoryRepository(db=None), 
    vector_repo=FAISSSemanticRepository()
)
crystallization_service = CrystallizationService(memory_service=memory_service)
