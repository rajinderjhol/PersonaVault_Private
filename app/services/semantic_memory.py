from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select, delete
from app.models import SemanticPattern as SemanticPatternModel
from app.schemas.memory_schemas import SemanticPattern
from typing import List, Union

class SemanticMemory:
    """Long-term knowledge from learned patterns."""
    
    def __init__(self, db: Union[AsyncSession, async_sessionmaker[AsyncSession]]):
        self.db = db
    
    async def _get_session(self):
        """Internal helper to get a session if a factory was provided."""
        if callable(self.db):
            return self.db()
        return self.db

    async def get_patterns(self) -> List[SemanticPattern]:
        """Get all learned patterns."""
        session = await self._get_session()
        try:
            stmt = select(SemanticPatternModel)
            result = await session.execute(stmt)
            patterns = result.scalars().all()
            return [SemanticPattern(
                pattern_type=p.pattern_type,
                trigger=p.trigger,
                correction=p.correction,
                occurrence_count=p.occurrence_count
            ) for p in patterns]
        finally:
            if callable(self.db):
                await session.close()

    async def remove_pattern(self, trigger: str):
        """Remove a semantic pattern by its trigger string."""
        session = await self._get_session()
        try:
            stmt = delete(SemanticPatternModel).where(SemanticPatternModel.trigger == trigger)
            await session.execute(stmt)
            await session.commit()
        finally:
            if callable(self.db):
                await session.close()

    async def add_pattern(self, pattern: SemanticPattern):
        """Add a new semantic pattern."""
        session = await self._get_session()
        try:
            db_pattern = SemanticPatternModel(
                pattern_type=pattern.pattern_type,
                trigger=pattern.trigger,
                correction=pattern.correction,
                occurrence_count=pattern.occurrence_count
            )
            session.add(db_pattern)
            await session.commit()
        finally:
            if callable(self.db):
                await session.close()