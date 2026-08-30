"""
Swarm Agent Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from datetime import datetime

from app.db.session import get_db
from app.swarm.orchestrator import MultiAgentOrchestrator
from app.core.dependencies import require_admin
from app.models.user import User
import logging

router = APIRouter(prefix="/api/v1/swarm", tags=["swarm"])
logger = logging.getLogger(__name__)


@router.get("/agents")
async def list_agents(
    orchestrator: MultiAgentOrchestrator = Depends()
) -> List[Dict[str, Any]]:
    """List all agents with their status and configuration."""
    agents = orchestrator.get_agents()
    return [
        {
            "name": agent.name,
            "type": agent.__class__.__name__,
            "status": agent.status,
            "confidence": agent.confidence,
            "config": agent.config,
            "metrics": agent.metrics if hasattr(agent, 'metrics') else None
        }
        for agent in agents
    ]


@router.get("/agents/{agent_name}")
async def get_agent(
    agent_name: str,
    orchestrator: MultiAgentOrchestrator = Depends()
) -> Dict[str, Any]:
    """Get detailed information about a specific agent."""
    agent = orchestrator.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    
    return {
        "name": agent.name,
        "type": agent.__class__.__name__,
        "status": agent.status,
        "confidence": agent.confidence,
        "config": agent.config,
        "metrics": agent.metrics if hasattr(agent, 'metrics') else None,
        "capabilities": agent.capabilities if hasattr(agent, 'capabilities') else []
    }


@router.patch("/agents/{agent_name}")
async def update_agent_config(
    agent_name: str,
    config: Dict[str, Any],
    current_user: User = Depends(require_admin),
    orchestrator: MultiAgentOrchestrator = Depends()
) -> Dict[str, Any]:
    """Update agent configuration."""
    agent = orchestrator.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    
    try:
        updated = await orchestrator.update_agent_config(agent_name, config)
        return {
            "status": "success",
            "message": f"Agent {agent_name} configuration updated",
            "agent": updated
        }
    except Exception as e:
        logger.error(f"Failed to update agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_agent_metrics(
    orchestrator: MultiAgentOrchestrator = Depends()
) -> Dict[str, Any]:
    """Get aggregated agent metrics."""
    metrics = await orchestrator.get_metrics()
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_agents": len(metrics),
        "active_agents": sum(1 for m in metrics if m.get("status") == "active"),
        "agents": metrics
    }


@router.get("/negotiation-trace")
async def get_negotiation_trace(
    limit: int = 50,
    orchestrator: MultiAgentOrchestrator = Depends()
) -> List[Dict[str, Any]]:
    """Get recent agent negotiation traces."""
    traces = await orchestrator.get_negotiation_traces(limit)
    return traces
