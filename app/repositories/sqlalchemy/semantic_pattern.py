from typing import List, Any, Optional
from sqlalchemy.future import select
from sqlalchemy import delete
from app.models import SemanticPattern as SemanticPatternModel
from app.repositories.interfaces import ISemanticPatternRepository
from app.repositories.sqlalchemy.base import SQLBaseRepository
import logging

logger = logging.getLogger(__name__)

class SQLSemanticPatternRepository(SQLBaseRepository, ISemanticPatternRepository):
    """SQLAlchemy implementation for semantic patterns."""
    
    async def get_all(self) -> List[SemanticPatternModel]:
        session = await self._get_session()
        try:
            stmt = select(SemanticPatternModel)
            result = await session.execute(stmt)
            return result.scalars().all()
        finally:
            await self._close_session(session)

    async def list_patterns(self, limit: int, offset: int, domain: Optional[str] = None, min_confidence: float = 0.0, search: Optional[str] = None, sort_by: str = "weight", sort_order: str = "desc") -> List[SemanticPatternModel]:
        session = await self._get_session()
        try:
            stmt = select(SemanticPatternModel)
            
            if domain:
                stmt = stmt.where(SemanticPatternModel.pattern_type == domain)
            if min_confidence > 0:
                stmt = stmt.where(SemanticPatternModel.weight >= min_confidence)
            if search:
                stmt = stmt.where(SemanticPatternModel.trigger.contains(search))
            
            # Apply sorting
            order_by = getattr(SemanticPatternModel, sort_by)
            if sort_order == "desc":
                stmt = stmt.order_by(order_by.desc())
            else:
                stmt = stmt.order_by(order_by.asc())
                
            stmt = stmt.limit(limit).offset(offset)
            
            result = await session.execute(stmt)
            return result.scalars().all()
        finally:
            await self._close_session(session)

    async def count_patterns(self, domain: Optional[str] = None, min_confidence: float = 0.0, search: Optional[str] = None) -> int:
        session = await self._get_session()
        try:
            from sqlalchemy import func
            stmt = select(func.count(SemanticPatternModel.id))
            
            if domain:
                stmt = stmt.where(SemanticPatternModel.pattern_type == domain)
            if min_confidence > 0:
                stmt = stmt.where(SemanticPatternModel.weight >= min_confidence)
            if search:
                stmt = stmt.where(SemanticPatternModel.trigger.contains(search))
                
            result = await session.execute(stmt)
            return result.scalar_one()
        finally:
            await self._close_session(session)

    async def get_by_id(self, pattern_id: int) -> Optional[SemanticPatternModel]:
        session = await self._get_session()
        try:
            stmt = select(SemanticPatternModel).where(SemanticPatternModel.id == pattern_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        finally:
            await self._close_session(session)


    async def add(self, pattern: Any) -> SemanticPatternModel:
        session = await self._get_session()
        try:
            data = pattern.dict() if hasattr(pattern, 'dict') else pattern
            db_pattern = SemanticPatternModel(
                pattern_type=data.get('pattern_type'),
                trigger=data.get('trigger'),
                correction=data.get('correction'),
                occurrence_count=data.get('occurrence_count', 1),
                weight=data.get('weight', 0.7),
                is_active=data.get('is_active', True)
            )
            session.add(db_pattern)
            await session.commit()
            await session.refresh(db_pattern)
            return db_pattern
        except Exception as e:
            await session.rollback()
            logger.error(f"SQLSemanticPatternRepository Add Error: {e}")
            raise
        finally:
            await self._close_session(session)

    async def remove(self, trigger: str) -> bool:
        session = await self._get_session()
        try:
            await session.execute(delete(SemanticPatternModel).where(SemanticPatternModel.trigger == trigger))
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"SQLSemanticPatternRepository Remove Error: {e}")
            return False
        finally:
            await self._close_session(session)
