"""
Blackboard Router - Cognitive shared memory access
"""
from fastapi import APIRouter, Depends, Request
from app.core.dependencies import require_admin

router = APIRouter(prefix="/blackboard", tags=["admin"])

@router.get("/snapshot")
async def get_blackboard_snapshot(
    request: Request,
    user_id: int = Depends(require_admin)
):
    """Get the current blackboard state (cognitive shared memory)."""
    blackboard = getattr(request.app.state, "blackboard", None)
    if blackboard:
        snapshot = blackboard.get_snapshot()
        return {
            "current_state": snapshot.get("current_state", {}),
            "active_agents": snapshot.get("active_agents", []),
            "conflict_history": snapshot.get("conflict_history", [])
        }
    return {"current_state": {}, "active_agents": [], "conflict_history": []}
