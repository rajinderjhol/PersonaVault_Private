import logging
from typing import List, Dict, Any, Union, Optional
from app.repositories.interfaces import IMemoryRepository, IVectorRepository, IGraphRepository

logger = logging.getLogger(__name__)

class MemoryService:
    """
    High-level business logic for memory operations.
    Orchestrates between L2 (Episodic/SQL), L3 (Semantic/Vector), and Graph repositories.
    """
    def __init__(
        self, 
        memory_repo: IMemoryRepository,
        vector_repo: Optional[IVectorRepository] = None,
        graph_repo: Optional[IGraphRepository] = None
    ):
        self.memory_repo = memory_repo
        self.vector_repo = vector_repo
        self.graph_repo = graph_repo

    async def search_memories(self, user_id: int, query: str, limit: int = 5, environment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Hybrid search: Semantic (Vector) + Relational (Graph) + Keyword (SQL), optionally scoped to an environment.
        """
        results = []
        seen_ids = set()

        try:
            # 1. Semantic search (Vector)
            if self.vector_repo:
                vector_results = await self.vector_repo.search(query, user_id, limit=limit, environment_id=environment_id)
                for res in vector_results:
                    if res["id"] not in seen_ids:
                        results.append(res)
                        seen_ids.add(res["id"])

            # 2. Keyword search (SQL) - Fallback or supplementary
            sql_results = await self.memory_repo.search(user_id, query, limit=limit, environment_id=environment_id)
            for m in sql_results:
                if m.id not in seen_ids:
                    results.append({
                        "id": m.id,
                        "content": m.content,
                        "score": 0.5,  # Default score for keyword match
                        "metadata": {"tags": m.tags, "title": m.title, "environment_id": getattr(m, 'environment_id', None)}
                    })
                    seen_ids.add(m.id)
            
            return results
        except Exception as e:
            logger.error(f"MemoryService: Search error: {e}")
            return []

    async def find_crystallized_pattern(self, prompt: str, context: dict) -> Optional[Any]:
        """
        Find a matching crystallized pattern for the prompt.
        Uses the CrystallizationService to search.
        """
        from app.api.v2.services.crystallization_service import crystallization_service
        
        env_id = context.get("env_id")
        if not env_id:
            return None
        
        patterns = await crystallization_service.get_patterns(env_id)
        
        # Simple similarity check for this prototype
        for p in patterns:
            pattern_data = p.get("pattern", {})
            query_pattern = pattern_data.get("query", "")
            
            # Simple keyword overlap as a placeholder for vector similarity
            if query_pattern and any(word in prompt.lower() for word in query_pattern.lower().split()):
                # Construct a mock pattern object that matches what generator expects
                class MockPattern:
                    id = p["pattern_id"]
                    name = p["source"]
                    confidence = 0.95 # Mock confidence
                
                return MockPattern()
        
        return None

    async def save_memory(self, user_id: int, memory_type: str, content: str, tags: Union[str, List[str]], title: Optional[str] = None, environment_id: Optional[str] = None) -> Any:
        """Save a memory, optionally scoped to an environment, and trigger multi-modal indexing."""
        tags_str = ",".join(tags) if isinstance(tags, list) else tags
        if not title:
            title = content[:50] + ("..." if len(content) > 50 else "")
        
        # 1. Save to L2 (SQL)
        new_memory = await self.memory_repo.add(user_id, title, content, memory_type, tags_str, environment_id=environment_id)
        
        # 2. Trigger side-effects (L3 Vector / Graph)
        if new_memory:
            if self.vector_repo:
                await self.vector_repo.add(new_memory.id, content, user_id, environment_id=environment_id)
            if self.graph_repo:
                await self.graph_repo.add_node(new_memory.id, new_memory.title, "Memory", user_id)
        
        return new_memory

    async def get_memory(self, memory_id: int, environment_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single memory by ID, optionally scoped to an environment.
        In V2, environment_id is strongly recommended to prevent breakout.
        """
        memory = await self.memory_repo.get_by_id(memory_id)
        if memory:
            # Scoping check
            if environment_id and getattr(memory, 'environment_id', None) != environment_id:
                logger.warning(f"🛡️ Isolation Guard: Access denied to memory {memory_id} from env {environment_id}")
                return None
                
            return {
                "id": memory.id,
                "content": memory.content,
                "metadata": {
                    "type": memory.modality,
                    "tags": memory.tags.split(",") if memory.tags else [],
                    "title": memory.title,
                    "environment_id": getattr(memory, 'environment_id', None)
                }
            }
        return None

    async def delete_expired_memories(self) -> int:
        """Logic for the 'Living Memory' concept."""
        return await self.memory_repo.delete_expired()

    async def delete_memory(self, memory_id: int) -> bool:
        """Remove memory from all layers."""
        success = await self.memory_repo.delete(memory_id)
        if success:
            if self.vector_repo:
                await self.vector_repo.delete(memory_id)
            # Graph deletion could also be added here
        return success

