from typing import List, Any
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
