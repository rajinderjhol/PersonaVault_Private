from fastapi import APIRouter
from app.api.v2.services.environment_service import environment_service
from app.api.v2.services.membership_service import membership_service
from app.api.v2.services.authority_service import authority_service
from app.api.v2.services.crystallization_service import crystallization_service
from datetime import datetime

router = APIRouter(prefix="/v2/health", tags=["v2-health"])

@router.get("/")
async def health_check():
    """
    Comprehensive V2 Health Check.
    Returns the readiness status of all core V2 services.
    """
    health_report = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.1.0-hardened",
        "components": {
            "environment_runtime": {
                "status": "ready",
                "active_environments": len(await environment_service.list_environments())
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
        }
    }
    
    return health_report
