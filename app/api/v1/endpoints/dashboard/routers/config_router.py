from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import logging

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.models import SystemConfig
from app.services.intelligence_gateway import gateway

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["admin"])

@router.get("/primary-ai-provider")
async def get_primary_ai_provider_dashboard(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get the current primary AI provider for the dashboard."""
    try:
        await gateway.ensure_initialized()
        stmt = select(SystemConfig).where(SystemConfig.key == "primary_ai_provider")
        result = await db.execute(stmt)
        config = result.scalars().first()
        return {"primary_provider": config.value if config else "ollama"}
    except Exception as e:
        logger.error(f"Error in get_primary_ai_provider_dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Cognitive Engine Error: {str(e)}")


@router.post("/primary-ai-provider")
async def update_primary_ai_provider_dashboard(
    request: Request,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update the primary AI provider and reload gateway config."""
    data = await request.json()
    provider = data.get("provider")

    stmt = select(SystemConfig).where(SystemConfig.key == "primary_ai_provider")
    result = await db.execute(stmt)
    config = result.scalars().first()
    if not config:
        config = SystemConfig(key="primary_ai_provider", value=provider)
        db.add(config)
    else:
        config.value = provider
    await db.commit()
    await gateway.reload_config()
    return {"status": "success", "new_primary_provider": provider}


@router.get("/ai-provider-settings/{provider}")
async def get_ai_provider_settings(
    provider: str,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get host and API key for a specific provider."""
    stmt = select(SystemConfig).where(SystemConfig.key.in_([
        f"ai_provider_{provider}_host", 
        f"ai_provider_{provider}_api_key",
        f"ai_provider_{provider}_model"
    ]))
    result = await db.execute(stmt)
    configs = result.scalars().all()
    res = {"host": "", "api_key": "", "model": ""}
    for c in configs:
        if "host" in c.key:
            res["host"] = c.value
        if "api_key" in c.key:
            res["api_key"] = c.value
        if "model" in c.key:
            res["model"] = c.value
    return res


@router.post("/ai-provider-settings")
async def update_ai_provider_settings(
    request: Request,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Save cloud API settings and reload gateway."""
    data = await request.json()
    provider = data.get("provider")
    if not provider:
        raise HTTPException(400, "Provider required")
    
    for key_suffix in ["host", "api_key", "model"]:
        val = data.get(key_suffix)
        db_key = f"ai_provider_{provider}_{key_suffix}"
        stmt = select(SystemConfig).where(SystemConfig.key == db_key)
        config = (await db.execute(stmt)).scalars().first()
        if not config:
            db.add(SystemConfig(key=db_key, value=str(val or "")))
        else:
            config.value = str(val or "")

    en_key = f"ai_provider_{provider}_enabled"
    stmt_en = select(SystemConfig).where(SystemConfig.key == en_key)
    config_en = (await db.execute(stmt_en)).scalars().first()
    if not config_en:
        db.add(SystemConfig(key=en_key, value="true"))
    else:
        config_en.value = "true"
    
    await db.commit()
    await gateway.reload_config()
    return {"status": "success"}


@router.get("/ai-providers/cloud")
async def list_cloud_providers(db: AsyncSession = Depends(get_db)):
    """List all configured cloud AI providers."""
    # Updated to look at the ai_providers JSON config
    stmt = select(SystemConfig).where(SystemConfig.key == "ai_providers")
    config = (await db.execute(stmt)).scalars().first()
    if not config:
        return []
    
    try:
        data = json.loads(config.value)
        providers = []
        for name, settings in data.items():
            if name == "ollama": continue
            providers.append({
                "name": name,
                "enabled": settings.get("enabled", False),
                "host": settings.get("host", ""),
                "model": settings.get("model", ""),
                "api_key": settings.get("api_key", "")
            })
        return providers
    except:
        return []


@router.delete("/ai-provider/{provider}")
async def delete_ai_provider(provider: str, db: AsyncSession = Depends(get_db)):
    """Delete a specific AI provider configuration."""
    stmt = select(SystemConfig).where(SystemConfig.key == "ai_providers")
    config = (await db.execute(stmt)).scalars().first()
    if config:
        try:
            data = json.loads(config.value)
            if provider in data:
                del data[provider]
                config.value = json.dumps(data)
                await db.commit()
                await gateway.reload_config()
        except:
            pass
    return {"status": "success"}


@router.post("/ai-provider-test")
async def test_ai_provider_connection(
    request: Request,
    user_id: int = Depends(require_admin)
):
    """Test connection for a specific provider with provided credentials."""
    data = await request.json()
    provider = data.get("provider")
    if not provider:
        raise HTTPException(400, "Provider required")
    
    result = await gateway.test_provider_connection(provider, data.get("host"), data.get("api_key"))
    return result


@router.post("/reload-api-keys")
async def reload_api_keys(
    request: Request,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Reload API keys from .env file and update the database.
    """
    import json
    from pathlib import Path
    
    try:
        env_path = Path(__file__).parent.parent.parent.parent.parent.parent / ".env"
        if not env_path.exists():
            env_path = Path.cwd() / ".env"
        if not env_path.exists():
            return {"error": ".env file not found"}
        
        env_vars = {}
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
        
        api_keys = {}
        groq_key = env_vars.get('GROQ_API_KEY')
        if groq_key and groq_key != 'YOUR_GROQ_API_KEY':
            api_keys['groq'] = {
                'enabled': True,
                'host': 'https://api.groq.com/openai/v1',
                'model': 'qwen/qwen3.6-27b',
                'api_key': groq_key
            }
        
        gemini_key = env_vars.get('GEMINI_API_KEY')
        if gemini_key and gemini_key != 'YOUR_GEMINI_API_KEY':
            api_keys['gemini'] = {
                'enabled': True,
                'host': 'https://generativelanguage.googleapis.com/v1beta',
                'model': 'gemini-2.0-flash-exp',
                'api_key': gemini_key
            }
        
        deepseek_key = env_vars.get('DEEPSEEK_API_KEY')
        if deepseek_key and deepseek_key != 'YOUR_DEEPSEEK_API_KEY':
            api_keys['deepseek'] = {
                'enabled': True,
                'host': 'https://api.deepseek.com/v1',
                'model': 'deepseek-chat',
                'api_key': deepseek_key
            }
        
        if not api_keys:
            return {
                "status": "no_keys_found",
                "message": "No API keys found in .env file.",
                "env_vars_found": list(env_vars.keys())
            }
        
        stmt = select(SystemConfig).where(SystemConfig.key == "ai_providers")
        result = await db.execute(stmt)
        config = result.scalars().first()
        
        if config:
            try:
                current = json.loads(config.value)
            except:
                current = {}
            
            if 'ollama' not in current:
                current['ollama'] = {
                    'enabled': True,
                    'host': 'http://localhost:11434',
                    'model': 'tinydolphin:latest'
                }
            
            for provider, settings in api_keys.items():
                current[provider] = settings
            
            config.value = json.dumps(current)
            await db.commit()
            
            await gateway._apply_config_async(db)
            
            return {
                "status": "success",
                "message": f"✅ Loaded {len(api_keys)} API key(s) from .env",
                "providers_loaded": list(api_keys.keys()),
                "env_vars_found": list(env_vars.keys())
            }
        else:
            new_config = {'ollama': {'enabled': True, 'host': 'http://localhost:11434', 'model': 'tinydolphin:latest'}}
            for provider, settings in api_keys.items():
                new_config[provider] = settings
            
            new_system_config = SystemConfig(
                key="ai_providers",
                value=json.dumps(new_config)
            )
            db.add(new_system_config)
            await db.commit()
            
            return {
                "status": "success",
                "message": f"✅ Created new config with {len(api_keys)} API key(s) from .env",
                "providers_loaded": list(api_keys.keys())
            }
            
    except Exception as e:
        await db.rollback()
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/refresh-gateway")
async def refresh_gateway_config(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Refresh the gateway configuration from the database."""
    await gateway.reload_config()
    return {"status": "success", "message": "Gateway configuration reloaded"}

@router.get("/ai-provider-stats/all")
async def get_all_provider_stats(user_id: int = Depends(require_admin)):
    """Return rate limit statistics for all configured providers."""
    providers = ["groq", "ollama", "gemini", "deepseek"]
    stats = {}
    for provider in providers:
        try:
            stats[provider] = await RateLimitService.get_stats(provider)
        except Exception:
            stats[provider] = {"error": "Not configured"}
    return stats
