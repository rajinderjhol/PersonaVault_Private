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
            db_pattern = SemanticPatternModel(
                pattern_type=getattr(pattern, 'pattern_type', 'general'),
                trigger=getattr(pattern, 'trigger', ''),
                correction=getattr(pattern, 'correction', ''),
                occurrence_count=getattr(pattern, 'occurrence_count', 1),
                weight=getattr(pattern, 'weight', 0.7),
                is_active=getattr(pattern, 'is_active', True)
            )
            # Handle extra_data if it exists
            if hasattr(pattern, 'extra_data') and pattern.extra_data:
                db_pattern.extra_data = pattern.extra_data
            
            session.add(db_pattern)
            await session.commit()
            await session.refresh(db_pattern)
            return db_pattern
        except Exception as e:
            await session.rollback()
            logger.error(f'SQLSemanticPatternRepository Add Error: {e}')
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
