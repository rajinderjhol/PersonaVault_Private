from datetime import datetime, timezone
from typing import List, Optional, Any
from sqlalchemy.future import select
from sqlalchemy import delete, or_
from app.models import Memory
from app.repositories.interfaces import IMemoryRepository
from app.repositories.sqlalchemy.base import SQLBaseRepository
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

class SQLMemoryRepository(SQLBaseRepository, IMemoryRepository):
    """SQLAlchemy implementation for L2 memory."""
    
    async def add(self, user_id: int, title: str, content: str, modality: str, tags: str, environment_id: Optional[str] = None) -> Memory:
        session = await self._get_session()
        try:
            new_memory = Memory(
                user_id=user_id,
                title=title,
                content=content,
                tags=tags,
                modality=modality,
                environment_id=environment_id
            )
            session.add(new_memory)
            await session.commit()
            await session.refresh(new_memory)
            return new_memory
        except Exception as e:
            await session.rollback()
            logger.error(f"SQLMemoryRepository Add Error: {e}")
            raise
        finally:
            await self._close_session(session)

    async def get_by_id(self, memory_id: int) -> Optional[Memory]:
        session = await self._get_session()
        try:
            stmt = select(Memory).where(Memory.id == memory_id)
            result = await session.execute(stmt)
            return result.scalars().first()
        finally:
            await self._close_session(session)

    async def search(self, user_id: int, query: str, limit: int = 5, environment_id: Optional[str] = None) -> List[Memory]:
        session = await self._get_session()
        try:
            filters = [
                Memory.user_id == user_id,
                or_(
                    Memory.content.ilike(f"%{query}%"),
                    Memory.tags.ilike(f"%{query}%"),
                    Memory.title.ilike(f"%{query}%")
                )
            ]
            if environment_id:
                filters.append(Memory.environment_id == environment_id)
            
            stmt = select(Memory).where(*filters).limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()
        finally:
            await self._close_session(session)

    async def delete_expired(self) -> int:
        session = await self._get_session()
        try:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            stmt = select(Memory).where(Memory.expiry_days > 0)
            res = await session.execute(stmt)
            candidates = res.scalars().all()
            
            count = 0
            for m in candidates:
                if m.created_at + timedelta(days=m.expiry_days) < now:
                    await session.delete(m)
                    count += 1
            
            if count > 0:
                await session.commit()
            return count
        finally:
            await self._close_session(session)

    async def delete(self, memory_id: int) -> bool:
        session = await self._get_session()
        try:
            await session.execute(delete(Memory).where(Memory.id == memory_id))
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"SQLMemoryRepository Delete Error: {e}")
            return False
        finally:
            await self._close_session(session)
