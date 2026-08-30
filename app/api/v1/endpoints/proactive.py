"""
Proactive Intelligence API - Anticipate user needs and provide insights
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.proactive_intelligence import ProactiveIntelligenceService

router = APIRouter(prefix="/api/v1/proactive", tags=["proactive"])


@router.get("/insights")
async def get_proactive_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get proactive insights for the current user."""
    service = ProactiveIntelligenceService(db)
    insights = await service.get_insights(current_user)
    
    return {
        "insights": insights,
        "timestamp": datetime.utcnow().isoformat(),
        "count": len(insights)
    }


@router.post("/insights/{insight_id}/dismiss")
async def dismiss_insight(
    insight_id: str,
    current_user: User = Depends(get_current_user)
):
    """Dismiss a proactive insight."""
    # In production, store this in User preferences
    return {"status": "success", "message": "Insight dismissed"}


@router.post("/insights/{insight_id}/action")
async def take_action_on_insight(
    insight_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Take action on a proactive insight."""
    # Route to appropriate action based on insight type
    return {"status": "success", "message": "Action initiated"}
