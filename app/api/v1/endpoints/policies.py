"""
Policy management API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import require_admin
from app.services.auto_policy import AutoPolicyUpdater

router = APIRouter(prefix="/api/v1/admin/policies", tags=["admin"])

@router.post("/update")
async def update_policies(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger auto-policy update."""
    updater = AutoPolicyUpdater(db)
    return await updater.update_policies()

@router.get("/status")
async def get_policy_status(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get policy status."""
    updater = AutoPolicyUpdater(db)
    return await updater.get_policy_status()

@router.get("/recommendations")
async def get_policy_recommendations(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get policy recommendations."""
    updater = AutoPolicyUpdater(db)
    return await updater.get_policy_recommendations()
