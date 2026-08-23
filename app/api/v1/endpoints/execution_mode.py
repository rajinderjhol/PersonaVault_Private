"""
Execution Mode API - Switch modes at runtime.
"""
from fastapi import APIRouter, Depends
from app.core.dependencies import require_admin
from app.services.execution_modes import ExecutionMode, ExecutionModeManager

router = APIRouter(prefix="/api/v1/mode", tags=["mode"])

@router.get("/current")
async def get_current_mode():
    """Get the current execution mode."""
    return {
        "mode": ExecutionModeManager.get_mode().value,
        "config": ExecutionModeManager.get_config()
    }

@router.post("/set")
async def set_mode(
    mode: str,
    user_id: int = Depends(require_admin)
):
    """Set the execution mode."""
    mode_map = {
        "standard": ExecutionMode.STANDARD,
        "restricted": ExecutionMode.RESTRICTED,
        "simulation": ExecutionMode.SIMULATION,
        "audit": ExecutionMode.AUDIT
    }
    if mode not in mode_map:
        return {"error": f"Invalid mode. Use: {list(mode_map.keys())}"}
    
    ExecutionModeManager.set_mode(mode_map[mode])
    return {"status": "success", "mode": mode}
