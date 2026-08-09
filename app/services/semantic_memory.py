from typing import List, Any, Optional
from app.repositories.interfaces import ISemanticPatternRepository

class SemanticMemory:
    """Long-term knowledge from learned patterns. Orchestrates pattern management."""
    
    def __init__(self, repository: ISemanticPatternRepository):
        self.repository = repository
    
    async def get_patterns(self) -> List[Any]:
        """Get all learned patterns via the repository."""
        return await self.repository.get_all()

    async def get_patterns_by_similarity(self, query_embedding: List[float], threshold: float = 0.7) -> List[Any]:
        """
        Fetch patterns based on semantic similarity of triggers (Phase 4 readiness).
        Currently falls back to retrieving all patterns.
        """
        return await self.repository.get_all()

    async def remove_pattern(self, trigger: str):
        """Remove a semantic pattern by its trigger string via the repository."""
        return await self.repository.remove(trigger)

    async def add_pattern(self, pattern: Any):
        """Add a new semantic pattern via the repository."""
        return await self.repository.add(pattern)