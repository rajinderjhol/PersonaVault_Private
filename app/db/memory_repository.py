from typing import List, Optional, Any, Dict, Union
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy import delete
from app.models import Memory
from app.core.base_memory import AbstractMemoryRepository
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

class SQLMemoryRepository(AbstractMemoryRepository):
    """
    Concrete implementation of Memory Repository using SQLAlchemy and FAISS.
    This represents the 'Converged' infrastructure mode.
    """
    def __init__(self, 
                 db: Union[AsyncSession, async_sessionmaker[AsyncSession]], 
                 vector_service: Optional[Any] = None, 
                 graph_service: Optional[Any] = None):
        self.db = db
        self.vector_service = vector_service
        self.graph_service = graph_service

    async def _get_session(self) -> AsyncSession:
        if callable(self.db):
            return self.db()
        return self.db

    async def add(self, user_id: int, content: str, modality: str, tags: str) -> Memory:
        session = await self._get_session()
        is_factory = callable(self.db)
        try:
            new_memory = Memory(
                user_id=user_id,
                title=content[:50] + ("..." if len(content) > 50 else ""),
                content=content,
                tags=tags,
                modality=modality
            )
            session.add(new_memory)
            await session.commit()
            await session.refresh(new_memory)

            # Trigger side-effects (Vector/Graph)
            if self.vector_service:
                await self.vector_service.index_memory(new_memory.id, content, user_id)
            if self.graph_service:
                self.graph_service.create_memory_node(new_memory.id, new_memory.title, user_id)

            return new_memory
        except Exception as e:
            await session.rollback()
            logger.error(f"Repository Add Error: {e}")
            raise
        finally:
            if is_factory:
                await session.close()

    async def search(self, user_id: int, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        # 1. Try Vector Search first
        if self.vector_service:
            results = await self.vector_service.search_similar(query, user_id, limit=limit)
            if results:
                return results

        # 2. Fallback to SQL ilike
        session = await self._get_session()
        is_factory = callable(self.db)
        try:
            stmt = select(Memory).where(
                Memory.user_id == user_id,
                (Memory.content.ilike(f"%{query}%")) | (Memory.tags.ilike(f"%{query}%"))
            ).limit(limit)
            result = await session.execute(stmt)
            memories = result.scalars().all()
            return [{
                "id": m.id,
                "content": m.content,
                "score": 0.5,  # Default score for keyword match
                "metadata": {"tags": m.tags}
            } for m in memories]
        finally:
            if is_factory:
                await session.close()

    async def delete_expired(self) -> int:
        session = await self._get_session()
        is_factory = callable(self.db)
        try:
            now = datetime.now(timezone.utc)
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
            if is_factory:
                await session.close()

    async def delete_by_id(self, memory_id: int) -> bool:
        session = await self._get_session()
        is_factory = callable(self.db)
        try:
            await session.execute(delete(Memory).where(Memory.id == memory_id))
            await session.commit()
            return True
        finally:
            if is_factory:
                await session.close()