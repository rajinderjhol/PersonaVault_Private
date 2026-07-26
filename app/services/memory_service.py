import logging
from typing import List, Dict, Any, Union
from app.core.base_memory import AbstractMemoryRepository

logger = logging.getLogger(__name__)

class MemoryService:
    """
    High-level business logic for memory operations.
    Now decoupled from data access via the Repository Pattern.
    """
    def __init__(self, repository: AbstractMemoryRepository):
        self.repository = repository
        # Backwards compatibility for callers needing direct access to DB factory
        self.db = getattr(repository, 'db', None) 

    async def search_memories(self, user_id: int, query: str) -> List[Dict[str, Any]]:
        """
        Hybrid search: Semantic (Vector) + Relational (Graph) + Keyword (SQL).
        """
        try:
            return await self.repository.search(user_id, query)
        except Exception as e:
            logger.error(f"MemoryService: Search error: {e}")
            return []

    async def save_memory(self, user_id: int, memory_type: str, content: str, tags: Union[str, List[str]]) -> Any:
        """Save a memory and trigger multi-modal indexing."""
        tags_str = ",".join(tags) if isinstance(tags, list) else tags
        return await self.repository.add(user_id, content, memory_type, tags_str)
    
    async def create_memory_entry(self, user_id: int, title: str, content: str, tags: str, memory_id: int):
        """Legacy trigger for manual indexing. Deprecated."""
        pass

    async def delete_expired_memories(self):
        """Logic for the 'Living Memory' concept."""
        return await self.repository.delete_expired()
