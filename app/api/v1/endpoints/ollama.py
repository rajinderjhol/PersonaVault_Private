import httpx
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models import AISetting
from app.services.memory_service import MemoryService
from app.services.vault import vault
from app.core.dependencies import get_current_user
from app.config import Config
from app.schemas.memory_schemas import AISettingsCreate, ChatRequest, MemorySearchRequest

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get('/models')
async def get_models(request: Request, current_user: int = Depends(get_current_user)):
    try:
        client = request.app.state.ai_client
        response = await client.get(f"{Config.OLLAMA_BASE_URL}/api/tags", timeout=5.0)
        response.raise_for_status()
        
        installed_models = response.json().get('models', [])
        model_list = [{
            "model_name": m['name'],
            "provider_type": "Ollama",
            "description": m.get('details', {}).get('family', 'Local model')
        } for m in installed_models]
        return {"models": model_list}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Ollama service unreachable")

@router.post('/chat')
async def chat_completion(chat_req: ChatRequest, request: Request, current_user: int = Depends(get_current_user)):
    async def stream_generator():
        client = request.app.state.ai_client
        async with client.stream(
            "POST", f"{Config.OLLAMA_BASE_URL}/api/chat",
            json=chat_req.dict(), timeout=None
        ) as response:
            async for chunk in response.aiter_bytes():
                yield chunk
    return StreamingResponse(stream_generator(), media_type="application/x-ndjson")

@router.post('/search-memories')
async def search_memories(search_req: MemorySearchRequest, request: Request, db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    service = request.app.state.memory_service
    results = await service.search_memories(user_id=current_user, query=search_req.query)
    return {"results": results, "query": search_req.query, "timestamp": datetime.utcnow().isoformat()}

@router.get("/settings")
async def get_current_settings(
    current_user: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current active settings for user"""
    stmt = select(AISetting).where(
        AISetting.user_id == current_user,
        AISetting.is_active == True
    ).order_by(AISetting.created_at.desc())
    
    result = await db.execute(stmt)
    setting = result.scalars().first()
    
    if not setting:
        return {"message": "No settings found", "settings": None}
    
    return {
        "id": setting.id,
        "profile_name": setting.profile_name,
        "provider_type": setting.provider_type,
        "model_name": setting.model_name,
        "deployment_type": setting.deployment_type,
        "parameters": setting.parameters,
        "created_at": setting.created_at.isoformat() if setting.created_at else None
    }

@router.get("/settings/past")
async def get_past_settings(
    current_user: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get historical settings for user"""
    stmt = select(AISetting).where(
        AISetting.user_id == current_user
    ).order_by(AISetting.created_at.desc())
    
    result = await db.execute(stmt)
    settings = result.scalars().all()
    
    return [{
        "id": s.id,
        "profile_name": s.profile_name,
        "provider_type": s.provider_type,
        "model_name": s.model_name,
        "deployment_type": s.deployment_type,
        "is_active": s.is_active,
        "created_at": s.created_at.isoformat() if s.created_at else None
    } for s in settings]

@router.post("/test-connection")
async def test_connection(
    request: Request,
    base_url: Optional[str] = Body(None, embed=True),
    current_user: int = Depends(get_current_user)
):
    """Test connection to Ollama"""
    try:
        base_url = base_url or Config.OLLAMA_BASE_URL
        client = request.app.state.ai_client
        response = await client.get(f"{base_url}/api/tags", timeout=5.0)
        if response.status_code == 200:
            return {"status": "connected", "message": "Successfully connected to Ollama"}
        else:
            return {"status": "error", "message": f"Failed to connect: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}