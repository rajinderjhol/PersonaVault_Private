from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List
import json
import asyncio
from app.api.v2.models.environment import Environment
from app.api.v2.dependencies import require_membership
from app.swarm.orchestrator import get_orchestrator
from app.services.memory_service import MemoryService
from app.api.v2.services.authority_service import AuthorityService
from app.api.v2.services.crystallization_service import crystallization_service
from app.api.v2.services.prediction_service import PredictionService
from app.api.v2.services.simulation_service import SimulationService
from app.repositories.sqlalchemy.memory import SQLMemoryRepository
from app.repositories.faiss.vector import FAISSSemanticRepository

router = APIRouter(prefix="/{env_id}/agents", tags=["v2-agents"])

# Service Factory
def get_full_orchestrator():
    mem_repo = SQLMemoryRepository(db=None) 
    vec_repo = FAISSSemanticRepository()
    memory_service = MemoryService(memory_repo=mem_repo, vector_repo=vec_repo)
    authority_service = AuthorityService(membership_service=None) # Mock membership
    # Fixed shadowed name issue
    from app.api.v2.services.crystallization_service import crystallization_service as crystallization_svc
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

@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
async def list_agents(
    env_id: str,
    env: Environment = Depends(lambda env_id: require_membership(env_id))
):
    """List all available agents within the context of a specific environment."""
    # In a production system, this would query the orchestrator or registry
    # For now, return the standard swarm configuration
    return [
        {"id": "agent-orch-001", "name": "Orchestrator", "type": "orchestrator", "status": "active", "confidence": 0.98},
        {"id": "agent-reas-001", "name": "Reasoning Engine", "type": "reasoning", "status": "active", "confidence": 0.95},
        {"id": "agent-sec-001", "name": "Security Sentinel", "type": "policy", "status": "idle", "confidence": 0.92},
        {"id": "agent-mem-001", "name": "Memory Custodian", "type": "memory", "status": "active", "confidence": 0.99},
        {"id": "agent-act-001", "name": "Action Dispatcher", "type": "action", "status": "idle", "confidence": 0.90}
    ]

@router.post("/chat")
async def chat_with_agent(
    env_id: str,
    query: str,
    env: Environment = Depends(lambda env_id: require_membership(env_id)),
    orchestrator = Depends(get_full_orchestrator)
):
    """Chat with an agent within the context of a specific environment."""
    context = {"environment_id": env_id, "user_id": 1}
    return await orchestrator.process_query(query, user_id=1, provider="ollama")

@router.websocket("/ws")
async def agent_websocket(
    websocket: WebSocket,
    env_id: str,
):
    """WebSocket for real-time agent status updates."""
    await websocket.accept()
    try:
        while True:
            # Simulate real-time updates
            agents = [
                {"agentId": "agent-orch-001", "status": "active", "currentTask": "Monitoring Lattices"},
                {"agentId": "agent-reas-001", "status": "thinking", "currentTask": "Analyzing Pattern #402"},
                {"agentId": "agent-sec-001", "status": "idle"},
                {"agentId": "agent-mem-001", "status": "busy", "currentTask": "Crystallizing memories"},
                {"agentId": "agent-act-001", "status": "idle"}
            ]
            await websocket.send_text(json.dumps(agents))
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error in {env_id}: {e}")
        await websocket.close()
