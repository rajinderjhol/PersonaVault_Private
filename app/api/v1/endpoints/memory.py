from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
import logging
from app.db.session import get_db
from app.models import Memory, PersonalContext, IoTData
from .auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter()

class MemoryCreate(BaseModel):
    title: Optional[str] = None
    content: str
    tags: Optional[str] = ""
    expiry_days: Optional[int] = 0

class MemoryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None

@router.get("/")
async def get_memories(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Memory).where(Memory.user_id == user_id)
    result = await db.execute(stmt)
    memories = result.scalars().all()
    return [{
        "id": m.id,
        "title": m.title,
        "content": m.content[:200] + "..." if len(m.content) > 200 else m.content,
        "tags": m.tags,
        "created_at": m.created_at.isoformat() if m.created_at else None
    } for m in memories]

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from app.models import Memory
from app.repositories.sqlalchemy.memory import SQLMemoryRepository

@router.post("/")
async def create_memory(
    request: Request,
    memory: MemoryCreate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a memory with vector indexing via repository."""
    try:
        # Get memory service from app state (uses repository pattern)
        memory_service = request.app.state.memory_service
        
        # Save to L2 (SQL)
        new_memory = await memory_service.memory_repo.add(
            user_id=user_id,
            title=memory.title or "",
            content=memory.content,
            modality="text",
            tags=memory.tags or ""
        )
        
        # Offload side-effects (L3 Vector / Graph) to background tasks
        if new_memory:
            if memory_service.vector_repo:
                background_tasks.add_task(memory_service.vector_repo.add, new_memory.id, memory.content, user_id)
            if memory_service.graph_repo:
                background_tasks.add_task(memory_service.graph_repo.add_node, new_memory.id, new_memory.title, "Memory", user_id)
        
        return {
            "message": "Memory created with vector indexing (queued)", 
            "id": new_memory.id,
            "title": new_memory.title
        }
    except Exception as e:
        # Fallback: direct DB insert if service fails
        logger.error(f"Memory service error: {e}")
        new_memory = Memory(
            user_id=user_id,
            title=memory.title or "",
            content=memory.content,
            tags=memory.tags or "",
            expiry_days=memory.expiry_days or 0
        )
        db.add(new_memory)
        await db.commit()
        await db.refresh(new_memory)
        return {
            "message": "Memory created (fallback)", 
            "id": new_memory.id
        }
        return {"message": "Memory created (fallback)", "id": new_memory.id}

@router.get("/search")
async def search_memories(
    request: Request,
    query: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    if not query:
        return {"results": []}
    
    # Try semantic search first
    try:
        memory_service = request.app.state.memory_service
        results = await memory_service.search_memories(
            user_id=user_id,
            query=query
        )
        if results:
            return {"query": query, "results": results, "source": "semantic"}
    except Exception as e:
        logger.warning(f"Semantic search failed: {e}")
    
    # Fallback to keyword search
    search_pattern = f"%{query}%"
    stmt = select(Memory).where(
        Memory.user_id == user_id,
        (Memory.title.ilike(search_pattern) | Memory.content.ilike(search_pattern))
    )
    result = await db.execute(stmt)
    results = result.scalars().all()
    return {"query": query, "results": results, "source": "keyword"}
