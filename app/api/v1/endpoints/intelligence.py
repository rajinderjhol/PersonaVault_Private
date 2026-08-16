"""
Intelligence API endpoints.
"""
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.models import User
from app.services.intelligence_gateway import gateway
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])

@router.get("/status")
async def intelligence_status(
    user_id: int = Depends(get_current_user)
):
    """Get the current status of the Intelligence Gateway."""
    if not getattr(gateway, "_initialized_from_db", True):
        await gateway.reload_config()

    enabled_providers = [name for name, cfg in gateway.ai_tool.providers.items() if cfg.get("enabled")]
    
    return {
        "mode": gateway.config.get("router", {}).get("strategy", "hybrid"),
        "providers": enabled_providers,
        "databases": list(gateway.db_tool.connections.keys()),
        "files": len(gateway.file_tool.index),
        "packs": len(gateway.packs),
        "web_search": gateway.web_tool.enabled,
        "agent_swarm": gateway.agent_tool is not None
    }

@router.get("/providers")
async def get_providers(
    current_user: User = Depends(get_current_user)
):
    """Get list of available providers."""
    await gateway.ensure_initialized()
    providers = []
    for name, config in gateway.ai_tool.providers.items():
        if config.get("enabled", False):
            providers.append({
                "name": name,
                "status": "available",
                "model": config.get("model", "default")
            })
    return {"providers": providers}
