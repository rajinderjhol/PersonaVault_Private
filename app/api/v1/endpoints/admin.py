from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from uuid import UUID
from app.db.session import get_db
from app.models import SystemConfig, User
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

# --- User Management ---

@router.get("/users")
async def list_users(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """
    List all users (admin only).
    """
    try:
        stmt = select(User).offset(skip).limit(limit)
        result = await db.execute(stmt)
        users = result.scalars().all()
        
        count_stmt = select(func.count()).select_from(User)
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        return {
            "users": [
                {
                    "id": str(u.id),
                    "username": u.username,
                    "email": u.email,
                    "role": u.role,
                    "is_active": u.is_active,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                    "last_login": u.last_login.isoformat() if u.last_login else None
                }
                for u in users
            ],
            "total": total
        }
        
    except Exception as e:
        logger.error(f"List users failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")


@router.get("/users/{user_id}")
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific user (admin only).
    """
    try:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user")


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: UUID,
    role: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user role (admin only).
    """
    try:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if role not in ["admin", "analyst", "viewer"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        
        user.role = role
        await db.commit()
        await db.refresh(user)
        
        return {
            "status": "success",
            "message": f"User role updated to {role}",
            "user_id": str(user_id),
            "role": role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user role failed: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update user role")


@router.get("/roles")
async def list_roles(
    current_user: User = Depends(require_admin)
):
    """
    List all available roles.
    """
    return {
        "roles": [
            {"name": "admin", "description": "Full system access"},
            {"name": "analyst", "description": "Read/write access to intelligence"},
            {"name": "viewer", "description": "Read-only access"},
        ]
    }

# ... rest of existing admin endpoints ...

@router.get("/models")
async def list_models(
    current_user: User = Depends(require_admin)
):
    """
    List all available AI models.
    """
    try:
        # Check if Ollama is running
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                models = []
                for model in data.get("models", []):
                    models.append({
                        "name": model.get("name"),
                        "size": model.get("size"),
                        "modified_at": model.get("modified_at"),
                        "digest": model.get("digest"),
                    })
                return {"models": models, "provider": "ollama"}
            else:
                return {"models": [], "provider": "ollama", "error": "Ollama not responding"}
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        # Return Groq models as fallback
        return {
            "models": [
                {"name": "groq/llama3-70b", "provider": "groq"},
                {"name": "groq/mixtral-8x7b", "provider": "groq"},
                {"name": "groq/gemma-7b", "provider": "groq"},
            ],
            "provider": "groq"
        }


@router.post("/models/pull")
async def pull_model(
    model_name: str,
    current_user: User = Depends(require_admin)
):
    """
    Pull a model from Ollama.
    """
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:11434/api/pull",
                json={"name": model_name},
                timeout=60.0
            )
            if response.status_code == 200:
                return {"status": "success", "message": f"Model {model_name} pulled successfully"}
            else:
                return {"status": "error", "message": "Failed to pull model"}
    except Exception as e:
        logger.error(f"Failed to pull model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pull model: {str(e)}")

from datetime import datetime
# ... (imports) ...
# ...
@router.get("/config/primary-ai-provider")
async def get_primary_ai_provider(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current primary AI provider.
    """
    try:
        # Get the primary provider from config
        stmt = select(SystemConfig).where(SystemConfig.key == "primary_ai_provider")
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()
        
        if config:
            return {"provider": config.value, "config": config}
        
        # Fallback to default
        return {"provider": "groq", "config": None}
        
    except Exception as e:
        logger.error(f"Failed to get primary AI provider: {e}")
        raise HTTPException(status_code=500, detail="Failed to get primary AI provider")


@router.put("/config/primary-ai-provider")
async def update_primary_ai_provider(
    provider: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the primary AI provider.
    """
    try:
        # Validate provider
        valid_providers = ["groq", "ollama", "gemini", "auto"]
        if provider not in valid_providers:
            raise HTTPException(status_code=400, detail=f"Invalid provider. Must be one of: {valid_providers}")
        
        # Update or create config
        stmt = select(SystemConfig).where(SystemConfig.key == "primary_ai_provider")
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()
        
        if config:
            config.value = provider
            config.updated_at = datetime.utcnow()
        else:
            config = SystemConfig(
                key="primary_ai_provider",
                value=provider,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(config)
        
        await db.commit()
        await db.refresh(config)
        
        return {"status": "success", "provider": provider, "config": config}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update primary AI provider: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update primary AI provider")

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

from app.services.intelligence_gateway import gateway
...
@router.post("/models/set-active")
async def set_active_ollama_model(body: dict, user_id: int = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Set the active Ollama model."""
    model_name = body.get("model")
    if not model_name: raise HTTPException(status_code=400, detail="Model name required")
    
    stmt = select(SystemConfig).where(SystemConfig.key == "ai_provider_ollama_model")
    result = await db.execute(stmt)
    config = result.scalars().first()
    
    if not config:
        db.add(SystemConfig(key="ai_provider_ollama_model", value=model_name))
    else:
        config.value = model_name
        
    await db.commit()
    await gateway.reload_config()
    return {"status": "success"}

