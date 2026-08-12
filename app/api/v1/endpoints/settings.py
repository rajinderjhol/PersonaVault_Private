from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.system_config_repository import SystemConfigRepository
from app.utils.plugin_loader import PluginLoader
from typing import Dict, Any

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/tools")
async def get_tools(db: AsyncSession = Depends(get_db)):
    repo = SystemConfigRepository(db)
    # Get current saved config
    configs = await repo.get_config("plugins_config") or {}
    
    # Get all available plugins
    plugins = PluginLoader.load_plugins(plugins_dir="plugins")
    
    # Merge config
    result = []
    for p in plugins:
        result.append({
            "name": p["name"],
            "description": p["description"],
            "enabled": configs.get(p["name"], {}).get("enabled", True)
        })
    return {"tools": result}

from pydantic import BaseModel

class ToggleToolSchema(BaseModel):
    enabled: bool

@router.patch("/tools/{name}")
async def toggle_tool(name: str, payload: ToggleToolSchema, db: AsyncSession = Depends(get_db)):
    repo = SystemConfigRepository(db)
    configs = await repo.get_config("plugins_config") or {}
    
    configs[name] = {"enabled": payload.enabled}
    await repo.save_config("plugins_config", configs)
    
    # Trigger hot-reload to apply changes
    await gateway.hot_reload(db)
    
    return {"status": "success"}
