
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.db.session import get_db
from app.models import PersonalContext
from app.api.v1.endpoints.auth import get_current_user_id

router = APIRouter()

class ContextCreate(BaseModel):
    context_type: str  # 'location', 'activity', 'mood', 'environment'
    value: str
    associated_memory_id: Optional[int] = None

@router.post("/update")
async def update_context(
    context: ContextCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update the user's current context"""
    new_context = PersonalContext(
        user_id=user_id,
        context_type=context.context_type,
        value=context.value,
        associated_memory_id=context.associated_memory_id
    )
    db.add(new_context)
    await db.commit()
    return {"status": "context_updated", "id": new_context.id}

@router.get("/current")
async def get_current_context(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get the user's most recent context for each type"""
    context_types = ['location', 'activity', 'mood', 'environment']
    result = {}
    
    for ctx_type in context_types:
        stmt = select(PersonalContext).where(
            PersonalContext.user_id == user_id, 
            PersonalContext.context_type == ctx_type
        ).order_by(PersonalContext.created_at.desc())
        db_res = await db.execute(stmt)
        latest = db_res.scalars().first()
        
        if latest:
            result[ctx_type] = {
                "value": latest.value,
                "timestamp": latest.created_at.isoformat()
            }
    
    return {"context": result}

@router.get("/history")
async def get_context_history(
    context_type: Optional[str] = None,
    limit: int = 50,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get historical context data"""
    stmt = select(PersonalContext).where(PersonalContext.user_id == user_id)
    
    if context_type:
        stmt = stmt.where(PersonalContext.context_type == context_type)
    
    stmt = stmt.order_by(PersonalContext.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    results = result.scalars().all()
    
    return [{
        "context_type": c.context_type,
        "value": c.value,
        "timestamp": c.created_at.isoformat(),
        "associated_memory_id": c.associated_memory_id
    } for c in results]