"""
Swarm Status Endpoints - Real-time agent swarm visibility
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.swarm.orchestrator import MultiAgentOrchestrator

router = APIRouter(prefix="/api/v1/swarm", tags=["swarm"])

# Mock orchestration instance for API endpoint access
# In production this would likely be injected via dependency injection
orchestrator = MultiAgentOrchestrator(db_session=None, blackboard=None)

class SwarmConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: Dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = SwarmConnectionManager()

@router.get("/status")
async def get_swarm_status() -> Dict[str, Any]:
    """Get current swarm status."""
    return await orchestrator.get_swarm_status()

@router.get("/agents")
async def list_agents() -> List[Dict]:
    """List all agents in the swarm."""
    return await orchestrator.list_agents()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time swarm status updates."""
    await manager.connect(websocket)
    try:
        while True:
            status = await orchestrator.get_swarm_status()
            await websocket.send_json({
                "type": "swarm_status",
                "data": status,
                "timestamp": datetime.now().isoformat()
            })
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
