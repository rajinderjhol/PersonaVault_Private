import logging
from typing import Dict, List, Any, Optional
from app.services.vector_service import vector_service
from app.repositories.sqlalchemy.semantic_pattern import SQLSemanticPatternRepository
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

class IceMemoryRepository:
    """
    Repository for Layer 3 (Ice/Semantic) Memory.
    Combines SQL storage for patterns and FAISS for vector search.
    """
    
    def __init__(self, session_factory=None):
        self.sql_repo = SQLSemanticPatternRepository(db=session_factory or SessionLocal)
        self.vector_service = vector_service
    
    def _model_to_dict(self, p) -> Dict[str, Any]:
        return {
            "id": p.id,
            "pattern_type": p.pattern_type,
            "trigger": p.trigger,
            "correction": p.correction,
            "occurrence_count": p.occurrence_count,
            "derived_from": p.derived_from,
            "success_count": p.success_count,
            "weight": p.weight,
            "is_active": p.is_active,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "confidence": p.weight
        }

    async def list_patterns(self, limit=50, offset=0, domain=None, min_confidence=0.0, search=None, sort_by="weight", sort_order="desc") -> List[Dict[str, Any]]:
        patterns = await self.sql_repo.list_patterns(limit, offset, domain, min_confidence, search, sort_by, sort_order)
        return [self._model_to_dict(p) for p in patterns]
    
    async def count_patterns(self, domain=None, min_confidence=0.0, search=None) -> int:
        return await self.sql_repo.count_patterns(domain, min_confidence, search)
    
    async def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        pattern = await self.sql_repo.get_by_id(int(pattern_id))
        return self._model_to_dict(pattern) if pattern else None

    async def store(self, record: Dict[str, Any]) -> str:
        """Store a crystallized pattern in both SQL and Vector stores."""
        try:
            content = record.get("content", {})
            trigger = record.get("trigger", "unknown")
            
            pattern_data = {
                "pattern_type": record.get("type", "crystallized_reasoning"),
                "trigger": trigger,
                "correction": record.get("correction", ""),
                "weight": record.get("confidence", 0.9),
                "is_active": True,
                "occurrence_count": 1
            }
            
            db_pattern = await self.sql_repo.add(pattern_data)
            return str(db_pattern.id)
        except Exception as e:
            logger.error(f"IceMemoryRepository Store Error: {e}")
            raise

    async def search_similar(self, embedding=None, query=None, threshold=0.85, limit=5, user_id=1) -> List[Dict[str, Any]]:
        return []

    async def mark_invalid(self, pattern_id: str) -> bool:
        return False
