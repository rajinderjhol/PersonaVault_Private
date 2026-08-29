import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from app.services.vector_service import vector_service
from app.repositories.sqlalchemy.semantic_pattern import SQLSemanticPatternRepository

logger = logging.getLogger(__name__)

class IceMemoryRepository:
    """
    Repository for Layer 3 (Ice/Semantic) Memory.
    Combines SQL storage for patterns and FAISS for vector search.
    """
    
    def __init__(self, session_factory=None):
        self.sql_repo = SQLSemanticPatternRepository(session_factory)
        self.vector_service = vector_service
    
    async def store(self, record: Dict[str, Any]) -> str:
        """Store a crystallized pattern in both SQL and Vector stores."""
        try:
            # 1. Store in SQL
            content = record.get("content", {})
            trigger = content.get("query_pattern", record.get("trigger", "unknown"))
            
            pattern_data = {
                "pattern_type": record.get("type", "crystallized_reasoning"),
                "trigger": trigger,
                "correction": content.get("response", record.get("correction", "")),
                "weight": record.get("confidence", 0.9),
                "is_active": True,
                "occurrence_count": 1
            }
            
            db_pattern = await self.sql_repo.add(pattern_data)
            memory_id = db_pattern.id
            
            # 2. Store in Vector Store
            # If embedding is provided, use it, otherwise generate one
            raw_text = record.get("raw_text") or f"{trigger}\n{pattern_data['correction']}"
            
            # Note: vector_service.index_memory handles embedding generation
            # But we want to ensure it uses the same user_id
            user_id = record.get("user_id", 1)
            await self.vector_service.index_memory(
                memory_id=memory_id,
                content=raw_text,
                user_id=user_id
            )
            
            return str(memory_id)
        except Exception as e:
            logger.error(f"IceMemoryRepository Store Error: {e}")
            raise

    async def search_similar(self, embedding=None, query=None, threshold=0.85, limit=5, user_id=1) -> List[Dict[str, Any]]:
        """Search for similar crystallized patterns."""
        try:
            # If embedding is provided, we might need to modify vector_service to accept it
            # For now, we'll use search_similar with the query string
            if query:
                results = await self.vector_service.search_similar(query, user_id, limit)
                # Filter by threshold
                return [r for r in results if r.get("score", 0) >= threshold]
            return []
        except Exception as e:
            logger.error(f"IceMemoryRepository Search Error: {e}")
            return []

    async def list_patterns(self, limit=50, offset=0, domain=None, min_confidence=0.0, search=None, sort_by="weight", sort_order="desc") -> List[Dict[str, Any]]:
        """List crystallized patterns."""
        patterns = await self.sql_repo.list_patterns(limit, offset, domain, min_confidence, search, sort_by, sort_order)
        return [p.__dict__ for p in patterns]
    
    async def count_patterns(self, domain=None, min_confidence=0.0, search=None) -> int:
        """Count crystallized patterns."""
        return await self.sql_repo.count_patterns(domain, min_confidence, search)
    
    async def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific crystallized pattern."""
        pattern = await self.sql_repo.get_by_id(int(pattern_id))
        return pattern.__dict__ if pattern else None

    async def mark_invalid(self, pattern_id: str) -> bool:
        """
        Mark a crystallized pattern as invalid (for deletion).
        """
        try:
            from sqlalchemy import update
            from app.repositories.sqlalchemy.semantic_pattern import SemanticPattern
            
            # Using sql_repo's DB session or similar
            async with self.sql_repo.db() as session:
                stmt = (
                    update(SemanticPattern)
                    .where(SemanticPattern.id == int(pattern_id))
                    .values(is_valid=False)
                )
                await session.execute(stmt)
                await session.commit()
                
                logger.info(f"Marked pattern {pattern_id} as invalid")
                return True
        except Exception as e:
            logger.error(f"Failed to mark pattern {pattern_id} as invalid: {e}")
            return False


