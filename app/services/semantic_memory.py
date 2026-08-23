"""
Semantic Memory Service
"""
import logging
from typing import List, Dict, Any
from app.models.semantic import SemanticPattern
from sqlalchemy import select

logger = logging.getLogger(__name__)

class SemanticMemory:
    def __init__(self, db_session):
        self.db = db_session
    
    async def search(self, query: str, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            # Check if SemanticPattern exists in models
            stmt = select(SemanticPattern).limit(limit)
            result = await self.db.execute(stmt)
            patterns = result.scalars().all()
            return [{"content": p.trigger, "source": "semantic", "score": 1.0} for p in patterns]
        except Exception as e:
            logger.warning(f"Semantic search failed: {e}")
            return []
