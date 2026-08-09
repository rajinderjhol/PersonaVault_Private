from typing import List, Any
from sqlalchemy.future import select
from app.models import EpisodicEntry as EpisodicEntryModel
from app.repositories.interfaces import IEpisodicTaskRepository
from app.repositories.sqlalchemy.base import SQLBaseRepository
import logging

logger = logging.getLogger(__name__)

class SQLEpisodicTaskRepository(SQLBaseRepository, IEpisodicTaskRepository):
    """SQLAlchemy implementation for task histories."""
    
    async def store(self, entry: Any) -> EpisodicEntryModel:
        session = await self._get_session()
        try:
            # Assuming entry is either a Pydantic schema or a dict
            data = entry.dict() if hasattr(entry, 'dict') else entry
            
            db_entry = EpisodicEntryModel(
                query=data.get('query'),
                plan=data.get('plan'),
                results=data.get('results'),
                answer=data.get('answer'),
                evaluation=data.get('evaluation'),
                governance_receipt_id=data.get('governance_receipt_id'),
                signature=data.get('signature'),
                hitl_approved=data.get('hitl_approved', False),
                user_feedback=data.get('user_feedback'),
                timestamp=data.get('timestamp')
            )
            session.add(db_entry)
            await session.commit()
            await session.refresh(db_entry)
            return db_entry
        except Exception as e:
            await session.rollback()
            logger.error(f"SQLEpisodicTaskRepository Store Error: {e}")
            raise
        finally:
            await self._close_session(session)

    async def get_recent(self, limit: int = 10) -> List[EpisodicEntryModel]:
        session = await self._get_session()
        try:
            stmt = select(EpisodicEntryModel).order_by(EpisodicEntryModel.timestamp.desc()).limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()
        finally:
            await self._close_session(session)
