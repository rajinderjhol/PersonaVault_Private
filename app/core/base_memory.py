from abc import ABC, abstractmethod
from typing import List, Any, Optional, Dict

class AbstractMemoryRepository(ABC):
    """
    Interface for Memory Storage. 
    Allows switching between SQLite/FAISS and Weaviate/Neo4j.
    """
    
    @abstractmethod
    async def add(self, user_id: int, content: str, modality: str, tags: str) -> Any:
        """Store a new memory and return the created object/ID."""
        pass

    @abstractmethod
    async def search(self, user_id: int, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform hybrid search (semantic + keyword)."""
        pass

    @abstractmethod
    async def delete_expired(self) -> int:
        """Delete memories that have passed their expiry date."""
        pass

    @abstractmethod
    async def delete_by_id(self, memory_id: int) -> bool:
        """Remove a specific memory."""
        pass