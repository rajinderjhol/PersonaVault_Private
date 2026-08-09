from abc import ABC, abstractmethod
from typing import List, Any, Optional, Dict
from datetime import datetime

class IBaseRepository(ABC):
    """Base interface for all repositories."""
    pass

class IMemoryRepository(IBaseRepository):
    """Interface for Relational/Episodic Memory (Layer 2)."""
    
    @abstractmethod
    async def add(self, user_id: int, title: str, content: str, modality: str, tags: str) -> Any:
        pass

    @abstractmethod
    async def get_by_id(self, memory_id: int) -> Optional[Any]:
        pass

    @abstractmethod
    async def search(self, user_id: int, query: str, limit: int = 5) -> List[Any]:
        pass

    @abstractmethod
    async def delete_expired(self) -> int:
        pass

    @abstractmethod
    async def delete(self, memory_id: int) -> bool:
        pass

class IVectorRepository(IBaseRepository):
    """Interface for Vector/Semantic Memory (Layer 3)."""
    
    @abstractmethod
    async def add(self, memory_id: int, content: str, user_id: int) -> bool:
        pass

    @abstractmethod
    async def search(self, query: str, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def delete(self, memory_id: int) -> bool:
        pass

class IGraphRepository(IBaseRepository):
    """Interface for Relationship/Graph Memory."""
    
    @abstractmethod
    async def add_node(self, entity_id: int, entity_name: str, entity_type: str, user_id: int) -> bool:
        pass

    @abstractmethod
    async def add_relation(self, source_id: int, target_id: int, relation_type: str) -> bool:
        pass

    @abstractmethod
    async def get_neighbors(self, entity_id: int, depth: int = 1) -> List[Any]:
        pass

    @abstractmethod
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        pass

class IEpisodicTaskRepository(IBaseRepository):
    """Interface for Task History (Episodic Entries)."""
    
    @abstractmethod
    async def store(self, entry: Any) -> Any:
        pass

    @abstractmethod
    async def get_recent(self, limit: int = 10) -> List[Any]:
        pass

class ISemanticPatternRepository(IBaseRepository):
    """Interface for Semantic Patterns (Learning Layer)."""
    
    @abstractmethod
    async def get_all(self) -> List[Any]:
        pass

    @abstractmethod
    async def add(self, pattern: Any) -> Any:
        pass

    @abstractmethod
    async def remove(self, trigger: str) -> bool:
        pass
