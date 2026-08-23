"""
Service Registry API - Manage services at runtime.
"""
from fastapi import APIRouter, Depends
from app.core.dependencies import require_admin
from app.services.service_registry import ServiceRegistry

router = APIRouter(prefix="/api/v1/registry", tags=["registry"])

@router.get("/services")
async def list_services():
    """List all registered services."""
    return ServiceRegistry.list_services()

@router.post("/swap/{service_type}/{old_name}/{new_name}")
async def swap_service(
    service_type: str,
    old_name: str,
    new_name: str,
    user_id: int = Depends(require_admin)
):
    """Swap a service at runtime."""
    success = ServiceRegistry.swap(service_type, old_name, new_name)
    return {"status": "success" if success else "failed"}
