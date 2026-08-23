from fastapi import APIRouter, Depends, Request
from pathlib import Path
import os
import subprocess
import asyncio
import logging

from app.core.dependencies import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["admin"])

# ============ SYSTEM MAINTENANCE ============

@router.post("/simulation/toggle")
async def toggle_simulation(request: Request, user_id: int = Depends(require_admin)):
    """Toggle the IoT simulation."""
    # Note: _run_iot_simulation is defined in dashboard_router.py. 
    # For now we need to import or handle this carefully.
    from app.api.v1.endpoints.dashboard.dashboard_router import _run_iot_simulation
    
    if hasattr(request.app.state, "iot_sim_task") and request.app.state.iot_sim_task and not request.app.state.iot_sim_task.done():
        request.app.state.iot_sim_task.cancel()
        return {"status": "stopped"}

    request.app.state.iot_sim_task = asyncio.create_task(_run_iot_simulation())
    return {"status": "started"}


@router.post("/maintenance/purge-pip")
async def purge_pip_cache(user_id: int = Depends(require_admin)):
    """Purge pip cache to free up disk space."""
    subprocess.run(["pip", "cache", "purge"], check=False)
    return {"status": "success", "message": "Pip cache purged."}


@router.post("/maintenance/cleanup-logs")
async def cleanup_logs(user_id: int = Depends(require_admin)):
    """Clear engine logs."""
    log_file = "storage/logs/uvicorn.log"
    if os.path.exists(log_file):
        open(log_file, 'w').close()
    return {"status": "success", "message": "Logs cleared."}


@router.post("/maintenance/reset-vector")
async def reset_vector_index(user_id: int = Depends(require_admin)):
    """Reset the FAISS vector index."""
    storage_dir = Path("storage")
    index_file = storage_dir / "vector_index.faiss"
    metadata_file = storage_dir / "vector_metadata.pkl"
    if index_file.exists():
        index_file.unlink()
    if metadata_file.exists():
        metadata_file.unlink()
    return {"status": "success", "message": "Vector index reset."}
