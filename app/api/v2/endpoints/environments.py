from fastapi import APIRouter, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import asyncio
import uuid

from app.api.v2.models.environment import Environment
from app.api.v2.services.environment_service import environment_service
from app.api.v2.dependencies import require_authority, require_membership, get_authority_service, get_environment_service
from pydantic import BaseModel
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models import Memory
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.model_service import ModelService

router = APIRouter(tags=["v2-environments"])

class EnvironmentCreate(BaseModel):
    name: str
    owner_principal_id: str
    type: str = "standard"

# --- Helper: Service Factory for Swarm Orchestrator (Lazy Imports to avoid circularity) ---
def get_full_orchestrator():
    from app.swarm.orchestrator import get_orchestrator
    from app.services.memory_service import MemoryService
    from app.api.v2.services.authority_service import AuthorityService
    from app.api.v2.services.prediction_service import PredictionService
    from app.api.v2.services.simulation_service import SimulationService
    from app.repositories.sqlalchemy.memory import SQLMemoryRepository
    from app.repositories.faiss.vector import FAISSSemanticRepository
    from app.api.v2.services.crystallization_service import crystallization_service as crystallization_svc

    mem_repo = SQLMemoryRepository(db=None) 
    vec_repo = FAISSSemanticRepository()
    memory_service = MemoryService(memory_repo=mem_repo, vector_repo=vec_repo)
    authority_service = AuthorityService(membership_service=None)
    prediction_service = PredictionService(memory_service, crystallization_svc)
    simulation_service = SimulationService(prediction_service)
    
    return get_orchestrator(
        db_session=None,
        blackboard=None,
        memory_service=memory_service,
        authority_service=authority_service,
        crystallization_service=crystallization_svc,
        prediction_service=prediction_service,
        simulation_service=simulation_service
    )

from app.api.v2.endpoints.governance import router as governance_router
from app.api.v2.endpoints.lattice import router as lattice_router

# ...

# --- Core Environment Endpoints ---

router.include_router(governance_router, prefix="/{env_id}/governance")
router.include_router(lattice_router, prefix="/{env_id}/lattice")


@router.post("", response_model=Environment)
@router.post("/", response_model=Environment)
async def create_environment(
    env_in: EnvironmentCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new V2 Environment."""
    return await environment_service.create_environment(
        name=env_in.name,
        owner_id=env_in.owner_principal_id,
        type=env_in.type
    )

@router.get("")
@router.get("/")
async def list_environments(current_user: User = Depends(get_current_user)):
    """List all V2 Environments."""
    return await environment_service.list_environments()


@router.get("/{env_id}", response_model=Environment)
async def get_environment(
    env: Environment = Depends(require_membership)
):
    """Get a V2 Environment by ID (Membership check)."""
    return env

async def require_update_authority(
    env_id: str, 
    current_user: User = Depends(get_current_user),
    auth_service = Depends(get_authority_service),
    env_service = Depends(get_environment_service)
):
    return await require_authority(env_id, "update_environment", current_user, auth_service, env_service)

async def require_delete_authority(
    env_id: str, 
    current_user: User = Depends(get_current_user),
    auth_service = Depends(get_authority_service),
    env_service = Depends(get_environment_service)
):
    return await require_authority(env_id, "delete_environment", current_user, auth_service, env_service)

@router.put("/{env_id}", response_model=Environment)
async def update_environment(
    updates: dict,
    env: Environment = Depends(require_update_authority)
):
    """Update a V2 Environment (Authority check)."""
    return await environment_service.update_environment(env.id, updates)

@router.delete("/{env_id}")
async def delete_environment(
    env: Environment = Depends(require_delete_authority)
):
    """Delete a V2 Environment (Authority check)."""
    success = await environment_service.delete_environment(env.id)
    if not success:
        raise HTTPException(status_code=404, detail="Environment not found")
    return {"status": "deleted"}

# --- Environment Metrics & Thermodynamics ---

@router.get("/{env_id}/metrics", response_model=Dict[str, Any])
async def get_environment_metrics(
    env_id: str
):
    """Get metrics for the environment."""
    return {
        "total_memories": 1102,
        "active_sessions": 3,
        "crystallization_rate": 0.85,
        "storage_used": 256,
        "temporal": {"velocity": 0.5, "decay_rate": 0.2, "aging_patterns": 10},
        "provider": "ollama",
        "mode": "standard",
        "latency": 45,
        "confidence": 0.94
    }

@router.get("/{env_id}/thermodynamics", response_model=Dict[str, Any])
async def get_environment_thermodynamics(
    env_id: str,
    env: Environment = Depends(require_membership)
):
    """Get memory phase distribution for the environment."""
    return {
        "gas": 42,
        "liquid": 156,
        "ice": 892,
        "snowflakes": 12,
        "total": 1102,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/{env_id}/intelligence/growth", response_model=Dict[str, Any])
async def get_environment_growth(env_id: str):
    """Get intelligence growth metrics."""
    return {
        "totalMemories": 12500,
        "crystallizedCount": 850,
        "compressionRatio": 10000,
        "memoryHistory": [
            {"date": "2026-09-01", "count": 1000, "type": "memory"},
            {"date": "2026-09-02", "count": 2500, "type": "memory"},
            {"date": "2026-09-03", "count": 5000, "type": "memory"},
            {"date": "2026-09-04", "count": 7500, "type": "crystallized"},
            {"date": "2026-09-05", "count": 12500, "type": "crystallized"}
        ],
        "compressionHistory": []
    }

# --- Environment Documents ---

@router.get("/{env_id}/documents", response_model=List[Dict[str, Any]])
async def list_environment_documents(
    env_id: str,
    db: AsyncSession = Depends(get_db),
    env: Environment = Depends(require_membership)
):
    """List documents for the environment."""
    stmt = select(Memory).where(
        Memory.user_id == int(env.owner_principal_id),
        Memory.modality == "document"
    ).order_by(Memory.created_at.desc())
    
    result = await db.execute(stmt)
    documents = result.scalars().all()
    
    return [{
        "id": d.id,
        "name": d.title.replace("Document: ", ""),
        "type": d.extra_data.get("file_type", "unknown"),
        "size": d.extra_data.get("file_size", 0),
        "created_at": d.created_at.isoformat()
    } for d in documents]

# --- Environment Models ---

@router.get("/{env_id}/models/providers")
async def get_environment_model_providers(
    env_id: str,
    env: Environment = Depends(require_membership)
):
    """Get available AI providers for this environment."""
    return [
        {"id": "ollama", "name": "Ollama", "enabled": True},
        {"id": "groq", "name": "Groq", "enabled": True},
        {"id": "gemini", "name": "Gemini", "enabled": True},
    ]

@router.get("/{env_id}/models", response_model=Dict[str, Any])
@router.get("/{env_id}/models/", response_model=Dict[str, Any])
async def get_environment_models(
    env_id: str,
    request: Request,
    env: Environment = Depends(require_membership),
    db: AsyncSession = Depends(get_db)
):
    """Get all models for an environment."""
    service = ModelService(db, request.app.state.ai_client)
    data = await service.list_models()
    return {
        "models": data.get("models", []),
        "active_model": data.get("active_model")
    }

@router.get("/{env_id}/models/metrics", response_model=Dict[str, Any])
async def get_environment_model_metrics(
    env_id: str,
    env: Environment = Depends(require_membership)
):
    """Get model performance metrics for the environment."""
    return {
        "totalDecisions": 1247,
        "hitRate": "94%",
        "throughput": 12.4,
        "confidenceTrend": [
            {"label": "Mon", "value": 90}, {"label": "Tue", "value": 92},
            {"label": "Wed", "value": 91}, {"label": "Thu", "value": 94},
            {"label": "Fri", "value": 93}, {"label": "Sat", "value": 95},
            {"label": "Sun", "value": 94}
        ],
        "latencyTrend": [
            {"label": "Mon", "value": 60}, {"label": "Tue", "value": 55},
            {"label": "Wed", "value": 58}, {"label": "Thu", "value": 45},
            {"label": "Fri", "value": 50}, {"label": "Sat", "value": 48},
            {"label": "Sun", "value": 45}
        ]
    }

# --- Environment Agents & WebSocket ---

@router.get("/{env_id}/agents", response_model=List[Dict[str, Any]])
async def list_environment_agents(
    env_id: str,
    env: Environment = Depends(require_membership)
):
    """List all available agents for the environment."""
    return [
        {"id": "agent-orch-001", "name": "Orchestrator", "type": "orchestrator", "status": "active", "confidence": 0.98},
        {"id": "agent-reas-001", "name": "Reasoning Engine", "type": "reasoning", "status": "active", "confidence": 0.95},
        {"id": "agent-sec-001", "name": "Security Sentinel", "type": "policy", "status": "idle", "confidence": 0.92},
        {"id": "agent-mem-001", "name": "Memory Custodian", "type": "memory", "status": "active", "confidence": 0.99},
        {"id": "agent-act-001", "name": "Action Dispatcher", "type": "action", "status": "idle", "confidence": 0.90}
    ]

@router.post("/{env_id}/agents/chat")
async def chat_with_environment_agent(
    env_id: str,
    query: str,
    env: Environment = Depends(require_membership),
    orchestrator = Depends(get_full_orchestrator)
):
    """Chat with an agent in the environment context."""
    return await orchestrator.process_query(query, user_id=1, provider="ollama")
@router.websocket("/{env_id}/agents/ws")
async def environment_agent_websocket(
    websocket: WebSocket,
    env_id: str,
):
    """WebSocket for real-time agent status updates."""
    token = websocket.query_params.get("token")
    print(f"📡 WebSocket connection attempt for environment: {env_id}, token: {'present' if token else 'missing'}")

    await websocket.accept()
    print(f"✅ WebSocket connection accepted for environment: {env_id}")

    try:
        while True:
            # Simulate real-time updates
            agents = [
                {"agentId": "agent-orch-001", "name": "Orchestrator", "status": "active", "currentTask": "Monitoring Lattices", "lastActivity": datetime.utcnow().isoformat()},
                {"agentId": "agent-reas-001", "name": "Reasoning Engine", "status": "thinking", "currentTask": "Analyzing Pattern #402", "lastActivity": datetime.utcnow().isoformat()},
                {"agentId": "agent-sec-001", "status": "idle", "lastActivity": datetime.utcnow().isoformat()},
                {"agentId": "agent-mem-001", "name": "Memory Custodian", "status": "busy", "currentTask": "Crystallizing memories", "lastActivity": datetime.utcnow().isoformat()},
                {"agentId": "agent-act-001", "name": "Action Dispatcher", "status": "idle", "lastActivity": datetime.utcnow().isoformat()}
            ]
            await websocket.send_json(agents)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected for environment: {env_id}")
    except Exception as e:
        print(f"❌ WebSocket error in {env_id}: {e}")
        try:
            await websocket.close()
        except:
            pass
