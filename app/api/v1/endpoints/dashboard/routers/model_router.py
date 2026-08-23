from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import logging

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.models import SystemConfig
from app.config import Config
from app.services.rate_limit_service import RateLimitService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["admin"])

@router.get("/")
async def list_models(request: Request, user_id: int = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """List installed Ollama models and identify the active one from DB."""
    active_model = "tinydolphin"
    try:
        stmt = select(SystemConfig).where(SystemConfig.key == "ai_provider_ollama_model")
        result = await db.execute(stmt)
        config = result.scalars().first()
        if config:
            active_model = config.value
            
        logger.info(f"DEBUG: DB active model: {active_model}")
        
        res = await request.app.state.ai_client.get(f"{Config.OLLAMA_BASE_URL}/api/tags")
        data = res.json()
        logger.info(f"DEBUG: Ollama models from API: {data.get('models', [])}")
        return {
            "models": data.get("models", []),
            "active_model": active_model
        }
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return {"models": [], "active_model": active_model}


@router.post("/pull")
async def pull_model(request: Request, user_id: int = Depends(require_admin)):
    """Pull a new model from Ollama registry with streaming updates."""
    data = await request.json()
    model_name = data.get("name")
    if not model_name:
        raise HTTPException(status_code=400, detail="Model name is required")

    async def generate():
        try:
            async with request.app.state.ai_client.stream(
                "POST", 
                f"{Config.OLLAMA_BASE_URL}/api/pull",
                json={"name": model_name},
                timeout=None
            ) as response:
                async for chunk in response.aiter_text():
                    yield chunk
        except Exception as e:
            yield json.dumps({"error": str(e)})

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@router.delete("/{model_name}")
async def delete_model(model_name: str, request: Request, user_id: int = Depends(require_admin)):
    """Delete a model from Ollama."""
    try:
        res = await request.app.state.ai_client.request(
            "DELETE",
            f"{Config.OLLAMA_BASE_URL}/api/delete",
            json={"name": model_name}
        )
        if res.status_code == 200:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=res.status_code, detail="Failed to delete model")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set-active")
async def set_active_model(
    request: Request,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Set the active Ollama model."""
    try:
        data = await request.json()
        model_name = data.get("model")
        
        if not model_name:
            raise HTTPException(status_code=400, detail="Model name required")
        
        # Update or insert the active model
        stmt = select(SystemConfig).where(SystemConfig.key == "ai_provider_ollama_model")
        result = await db.execute(stmt)
        config = result.scalars().first()
        
        if config:
            config.value = model_name
        else:
            config = SystemConfig(key="ai_provider_ollama_model", value=model_name)
            db.add(config)
        
        await db.commit()
        
        # Also update the primary provider to use ollama
        stmt_provider = select(SystemConfig).where(SystemConfig.key == "primary_ai_provider")
        result_provider = await db.execute(stmt_provider)
        provider_config = result_provider.scalars().first()
        
        if provider_config:
            provider_config.value = "ollama"
        else:
            provider_config = SystemConfig(key="primary_ai_provider", value="ollama")
            db.add(provider_config)
        
        await db.commit()
        
        # Reload the intelligence gateway
        try:
            from app.services.intelligence_gateway import gateway
            await gateway.reload_config()
        except Exception as e:
            logger.warning(f"Gateway reload failed: {e}")
        
        return {"status": "success", "message": f"Active model set to {model_name}"}
        
    except Exception as e:
        logger.error(f"Error setting active model: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/provider-stats/{provider}")
async def get_provider_stats(provider: str, user_id: int = Depends(require_admin)):
    """Return rate limit statistics for a given provider."""
    try:
        return await RateLimitService.get_stats(provider)
    except Exception as e:
        logger.error(f"Error getting provider stats: {e}")
        return {"error": str(e)}
