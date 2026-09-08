from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v2.models.environment import Environment
from app.api.v2.dependencies import require_membership
from app.api.v1.endpoints.health import get_decision_health

router = APIRouter(prefix="/{env_id}/admin", tags=["v2-admin"])

class SystemHealth(BaseModel):
    status: str
    score: float
    components: Dict[str, Any]
    timestamp: datetime

class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    source: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

@router.get("/health", response_model=SystemHealth)
async def get_environment_health(
    env_id: str,
    db: AsyncSession = Depends(get_db),
    env: Environment = Depends(require_membership)
):
    """Get health status for the specific environment."""
    decision_health = await get_decision_health(db)
    
    return {
        "status": decision_health["overall"]["status"],
        "score": decision_health["overall"]["score"],
        "components": decision_health["components"],
        "timestamp": datetime.utcnow()
    }

@router.get("/logs", response_model=List[LogEntry])
async def get_environment_logs(
    env_id: str,
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = None,
    env: Environment = Depends(require_membership)
):
    """Get activity logs for the specific environment."""
    # Dummy logs for now
    return [
        {
            "timestamp": datetime.utcnow(),
            "level": "info",
            "message": f"Environment {env_id} initialized",
            "source": "system"
        },
        {
            "timestamp": datetime.utcnow(),
            "level": "info",
            "message": "Orchestrator heartbeat detected",
            "source": "orchestrator"
        }
    ]

@router.post("/mode")
async def set_execution_mode(
    env_id: str,
    request: Dict[str, str],
    env: Environment = Depends(require_membership)
):
    """Set the execution mode for the environment."""
    mode = request.get("mode")
    if mode not in ["standard", "restricted", "simulation", "audit"]:
        raise HTTPException(status_code=400, detail="Invalid execution mode")
    
    return {"status": "success", "mode": mode, "updated_at": datetime.utcnow()}
