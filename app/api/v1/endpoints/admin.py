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

@router.post("/learning/config")
async def update_learning_config(request: Request, user = Depends(require_admin)):
    """Update the configuration for the crystallization engine."""
    body = await request.json()
    task = getattr(request.app.state, 'consolidation_task', None)
    db = request.state.db
    
    if not task:
        raise HTTPException(status_code=500, detail="Task not initialized")

    if "batch_size" in body:
        val = int(body["batch_size"])
        task.batch_size = val
        cfg = (await db.execute(select(SystemConfig).where(SystemConfig.key == "graduation_batch_size"))).scalars().first()
        if not cfg: db.add(SystemConfig(key="graduation_batch_size", value=str(val)))
        else: cfg.value = str(val)
    if "interval_hours" in body:
        val = float(body["interval_hours"])
        task.interval_hours = val
        cfg = (await db.execute(select(SystemConfig).where(SystemConfig.key == "graduation_interval"))).scalars().first()
        if not cfg: db.add(SystemConfig(key="graduation_interval", value=str(val)))
        else: cfg.value = str(val)
    await db.commit()
    return {"status": "success"}

@router.post("/learning/trigger")
async def trigger_learning_cycle(request: Request, user = Depends(require_admin)):
    """Manually ignite a learning (crystallization) cycle."""
    task = getattr(request.app.state, 'consolidation_task', None)
    if not task:
        raise HTTPException(status_code=500, detail="Consolidation Engine not initialized")
        
    try:
        # Wake up the existing background loop rather than spawning an overlapping task
        task.trigger_event.set()
        return {"status": "success", "message": "Crystallization cycle triggered in background."}
    except Exception as e:
        logger.error(f"Failed to trigger learning: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cognitive-load")
async def get_cognitive_load(request: Request, user = Depends(require_admin)):
    """Returns the current number of active orchestration tasks and agent states."""
    orchestrator = getattr(request.app.state, "orchestrator", None)
    return {
        "active_tasks": getattr(orchestrator, "active_tasks", 0),
        "agent_activity": getattr(orchestrator, "agent_activity", {})
    }

@router.get("/empathy/status")
async def get_empathy_status(request: Request, user = Depends(require_admin)):
    """Returns the last mood and tone determined by the EmpathyAgent."""
    agent = getattr(request.app.state, "empathy_agent", None)
    return {
        "mood": getattr(agent, "last_mood", "unknown"),
        "tone": getattr(agent, "last_tone", "neutral")
    }

@router.get("/telemetry/health")
async def get_health_telemetry(request: Request, user = Depends(require_admin)):
    """Exposes current biometric data to the dashboard."""
    return getattr(request.app.state, "medical_adapter", None).last_reading if hasattr(request.app.state, "medical_adapter") else {}

@router.get("/mcp/tools")
async def list_mcp_tools(request: Request, user = Depends(require_admin)):
    """Exposes registered MCP tools."""
    server = getattr(request.app.state, "mcp_server", None)
    return await server.list_tools() if server else []
