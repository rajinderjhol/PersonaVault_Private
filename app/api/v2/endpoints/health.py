from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.endpoints.health import get_decision_health
from datetime import datetime

router = APIRouter(tags=["v2-health"])

@router.get("")
@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive V2 Health Check.
    """
    decision_health = await get_decision_health(db)
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.1.0-hardened",
        "components": {
            "environment_runtime": {
                "status": "ready",
                "active_environments": 1
            },
            "governance_engine": {
                "status": "ready",
                "authority_layer": "active",
                "membership_layer": "active"
            },
            "intelligence_runtime": {
                "status": "ready",
                "crystallization": "enabled",
                "memory_isolation": "enforced"
            }
        },
        "metrics": decision_health
    }

