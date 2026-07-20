from app.models import Memory
from datetime import datetime, timedelta
import logging
from typing import Optional, List, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select, delete

logger = logging.getLogger(__name__)

class MemoryService:
    def __init__(self, 
                 db: Union[AsyncSession, async_sessionmaker[AsyncSession]], 
                 vector_service: Optional[Any] = None, 
                 graph_service: Optional[Any] = None):
        self.db = db
        self.vector_service = vector_service
        self.graph_service = graph_service

    async def _get_session(self) -> AsyncSession:
        """Internal helper to get a session if a factory was provided."""
        if callable(self.db):
            return self.db()
        return self.db

    async def search_memories(self, user_id: int, query: str) -> List[Dict[str, Any]]:
        """
        Hybrid search: Semantic (Vector) + Relational (Graph) + Keyword (SQL).
        """
        try:
            # 1. Semantic search if available
            if self.vector_service:
                vector_results = await self.vector_service.search_similar(query, user_id, limit=5)
                if vector_results:
                    logger.info(f"MemoryService: Found {len(vector_results)} vector matches")
                    return vector_results

            # 2. Fallback to SQL keyword search
            session = await self._get_session()
            is_factory = callable(self.db)
            try:
                stmt = select(Memory).where(
                    Memory.user_id == user_id,
                    (Memory.content.ilike(f"%{query}%")) | (Memory.tags.ilike(f"%{query}%"))
                )
                result = await session.execute(stmt)
                results = result.scalars().all()
                
                return [{
                    "id": m.id,
                    "title": m.title,
                    "content": m.content,
                    "tags": m.tags,
                    "created_at": m.created_at.isoformat()
                } for m in results]
            finally:
                if is_factory:
                    await session.close()
        except Exception as e:
            logger.error(f"MemoryService: Search error: {e}")
            return []

    async def save_memory(self, user_id: int, memory_type: str, content: str, tags: Union[str, List[str]]) -> Memory:
        """Save a memory and trigger multi-modal indexing."""
        try:
            tags_str = ",".join(tags) if isinstance(tags, list) else tags
            new_memory = Memory(
                user_id=user_id,
                title=content[:50] + ("..." if len(content) > 50 else ""),
                content=content,
                tags=tags_str,
                modality=memory_type
            )
            session = await self._get_session()
            is_factory = callable(self.db)
            try:
                session.add(new_memory)
                await session.commit()
                await session.refresh(new_memory)
                
                logger.info(f"MemoryService: Saved new memory_id={new_memory.id} for user_id={user_id}")
                
                # Trigger semantic and relational indexing
                if self.vector_service or self.graph_service:
                    await self.create_memory_entry(user_id, new_memory.title, content, tags_str, new_memory.id)
                    
                return new_memory
            except Exception:
                await session.rollback()
                raise
            finally:
                if is_factory:
                    await session.close()
        except Exception as e:
            logger.error(f"MemoryService: Save error: {e}")
            raise
    
    async def create_memory_entry(self, user_id: int, title: str, content: str, tags: str, memory_id: int):
        """Create memory entry and index in vector and graph stores."""
        # Index in vector DB
        if self.vector_service:
            await self.vector_service.index_memory(memory_id, content, user_id)
            
        # Create node in graph DB
        if self.graph_service:
            self.graph_service.create_memory_node(memory_id, title, user_id)

    async def delete_expired_memories(self):
        """
        Logic for the 'Living Memory' concept: memories that fade or expire.
        """
        try:
            current_time = datetime.utcnow()
            
            session = await self._get_session()
            is_factory = callable(self.db)
            try:
                # Fetch candidates for expiration
                stmt = select(Memory).where(Memory.expiry_days > 0)
                result = await session.execute(stmt)
                candidates = result.scalars().all()
                
                count = 0
                for mem in candidates:
                    # Check if memory is actually expired
                    created_at = mem.created_at
                    expiry_duration = timedelta(days=mem.expiry_days)
                    expiration_time = created_at + expiry_duration
                    
                    if expiration_time < current_time:
                        await session.delete(mem)
                        count += 1
                
                if count > 0:
                    await session.commit()
                logger.info(f"Cleaned up {count} expired memories.")
                return count
            except Exception:
                await session.rollback()
                raise
            finally:
                if is_factory:
                    await session.close()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return 0
