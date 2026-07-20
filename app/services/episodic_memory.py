from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.models import EpisodicEntry as EpisodicEntryModel
from app.schemas.memory_schemas import EpisodicEntry
from typing import Union

class EpisodicMemory:
    """Task histories for learning patterns."""
    
    def __init__(self, db: Union[AsyncSession, async_sessionmaker[AsyncSession]]):
        self.db = db
    
    async def _get_session(self):
        """Internal helper to get a session if a factory was provided."""
        if callable(self.db):
            return self.db()
        return self.db

    async def store(self, entry: EpisodicEntry):
        """Store an episodic entry."""
        session = await self._get_session()
        try:
            db_entry = EpisodicEntryModel(
                query=entry.query,
                plan=entry.plan.dict(),
                results=[r.dict() for r in entry.results],
                answer=entry.answer,
                evaluation=entry.evaluation.dict() if entry.evaluation else None,
                governance_receipt_id=entry.governance_receipt_id,
                signature=entry.signature,
                hitl_approved=entry.hitl_approved,
                user_feedback=entry.user_feedback,
                timestamp=entry.timestamp
            )
            session.add(db_entry)
            await session.commit()
        finally:
            if callable(self.db):
                await session.close()

    async def get_recent(self, limit: int = 10):
        """Get recent episodic entries."""
        session = await self._get_session()
        try:
            stmt = select(EpisodicEntryModel).order_by(EpisodicEntryModel.timestamp.desc()).limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()
        finally:
            if callable(self.db):
                await session.close()