from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.session import get_db
from app.models import SystemConfig
from app.services.semantic_memory import SemanticMemory
from app.core.dependencies import require_admin
import logging
import json
import asyncio

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

class AIProviderUpdate(BaseModel):
    provider: str  # 'ollama' or 'gemini'

class BlacklistRequest(BaseModel):
    trigger: str

@router.get("/config/ai-provider")
async def get_primary_ai_provider(
    db: AsyncSession = Depends(get_db)
):
    """Get the current primary AI provider."""
    try:
        stmt = select(SystemConfig).where(SystemConfig.key == "primary_ai_provider")
        result = await db.execute(stmt)
        config = result.scalars().first()
        if config:
            return {"primary_provider": config.value, "source": "database"}
        return {"primary_provider": "ollama", "source": "default"}
    except Exception as e:
        logger.error(f"Error fetching AI provider: {e}")
        return {"primary_provider": "ollama", "source": "error", "error": str(e)}

@router.put("/config/ai-provider")
async def update_primary_ai_provider(
    payload: AIProviderUpdate,
    user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Switch the primary AI provider globally."""
    if payload.provider not in ["ollama", "gemini"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider. Must be 'ollama' or 'gemini'."
        )

    try:
        stmt = select(SystemConfig).where(SystemConfig.key == "primary_ai_provider")
        result = await db.execute(stmt)
        config = result.scalars().first()
        if not config:
            config = SystemConfig(key="primary_ai_provider", value=payload.provider)
            db.add(config)
        else:
            config.value = payload.provider
        
        await db.commit()
        logger.info(f"Admin switched primary AI provider to: {payload.provider}")
        return {"status": "success", "primary_provider": payload.provider}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating AI provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.get("/config")
async def get_all_configs(
    db: AsyncSession = Depends(get_db)
):
    """Get all system configurations."""
    try:
        stmt = select(SystemConfig)
        result = await db.execute(stmt)
        configs = result.scalars().all()
        return {"configs": [{"key": c.key, "value": c.value, "updated_at": c.updated_at} for c in configs]}
    except Exception as e:
        logger.error(f"Error fetching configs: {e}")
        return {"configs": [], "error": str(e)}

@router.delete("/learning/patterns")
async def degraduate_pattern(
    trigger: str,
    user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """De-graduate (remove) a pattern from Semantic Memory (Layer 3)."""
    try:
        semantic = SemanticMemory(db)
        await semantic.remove_pattern(trigger)
        logger.info(f"Admin de-graduated pattern trigger: {trigger}")
        return {"status": "success", "message": f"Pattern '{trigger}' removed from Layer 3."}
    except Exception as e:
        logger.error(f"Error de-graduating pattern: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to de-graduate pattern: {str(e)}"
        )

@router.get("/learning/blacklist")
async def get_graduation_blacklist(
    db: AsyncSession = Depends(get_db)
):
    """Get the list of triggers that are blocked from graduation."""
    stmt = select(SystemConfig).where(SystemConfig.key == "graduation_blacklist")
    result = await db.execute(stmt)
    config = result.scalars().first()
    return {"blacklist": json.loads(config.value) if config else []}

@router.post("/learning/blacklist")
async def add_to_blacklist(
    payload: BlacklistRequest,
    user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Prevent a specific trigger from ever being graduated again."""
    stmt = select(SystemConfig).where(SystemConfig.key == "graduation_blacklist")
    result = await db.execute(stmt)
    config = result.scalars().first()
    
    blacklist = json.loads(config.value) if config else []
    if payload.trigger not in blacklist:
        blacklist.append(payload.trigger)
        if not config:
            config = SystemConfig(key="graduation_blacklist", value=json.dumps(blacklist))
            db.add(config)
        else:
            config.value = json.dumps(blacklist)
        await db.commit()
    return {"status": "success", "blacklist": blacklist}

@router.delete("/learning/blacklist")
async def remove_from_blacklist(
    trigger: str,
    user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Remove a trigger from the graduation blacklist."""
    stmt = select(SystemConfig).where(SystemConfig.key == "graduation_blacklist")
    result = await db.execute(stmt)
    config = result.scalars().first()
    if config:
        blacklist = json.loads(config.value)
        if trigger in blacklist:
            blacklist.remove(trigger)
            config.value = json.dumps(blacklist)
            await db.commit()
    return {"status": "success", "message": f"Removed '{trigger}' from blacklist."}

@router.get("/learning/config")
async def get_learning_config(request: Request):
    """Get the current configuration for the crystallization engine."""
    # Access the config passed to the task in main.py
    task = getattr(request.app.state, 'consolidation_task', None)
    if task:
        return task.config
    return {"batch_size": 0, "interval_hours": 0, "status": "Task not initialized"}

@router.post("/learning/trigger")
async def trigger_learning_cycle(request: Request, user = Depends(require_admin)):
    """Manually ignite a learning (crystallization) cycle."""
    try:
        from app.services.task_service import episodic_reflection_task
        asyncio.create_task(episodic_reflection_task())
        return {"status": "success", "message": "Crystallization cycle triggered in background."}
    except Exception as e:
        logger.error(f"Failed to trigger learning: {e}")
        raise HTTPException(status_code=500, detail=str(e))
