"""
Predictive Intelligence API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import require_admin, get_current_user
from app.services.predictive import PredictiveIntelligence
from app.services.proactive_suggestions import ProactiveSuggestionEngine
from app.services.automated_decision import AutomatedDecisionEngine
from app.models.user import User
from typing import List, Dict

router = APIRouter(prefix="/api/v1/predictive", tags=["predictive"])

@router.get("/drift")
async def get_drift(
    domain: str = None,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get drift analysis."""
    service = PredictiveIntelligence(db)
    return await service.calculate_drift_score(domain)

@router.get("/risks")
async def get_risks(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get emerging risks."""
    service = PredictiveIntelligence(db)
    return await service.identify_emerging_risks()

@router.get("/insights")
async def get_insights(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get proactive insights."""
    service = PredictiveIntelligence(db)
    return await service.get_proactive_insights()

@router.get("/user/{user_id}")
async def get_user_predictions(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get predictions for a specific user."""
    service = PredictiveIntelligence(db)
    return await service.get_user_predictions(user_id)

@router.post("/team")
async def get_team_analysis(
    user_ids: List[int],
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get analysis for a team of users."""
    service = PredictiveIntelligence(db)
    return await service.get_team_analysis(user_ids)

@router.get("/suggestions")
async def get_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get proactive suggestions for the current user."""
    engine = ProactiveSuggestionEngine(db)
    return await engine.get_dashboard_suggestions(current_user.id)

@router.post("/suggestions/{suggestion_id}/dismiss")
async def dismiss_suggestion(
    suggestion_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Dismiss a suggestion."""
    engine = ProactiveSuggestionEngine(db)
    return await engine.dismiss_suggestion(suggestion_id, current_user.id)

@router.post("/automate")
async def execute_automated_decision(
    decision: Dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Execute a decision automatically."""
    engine = AutomatedDecisionEngine(db)
    return await engine.execute_automated_decision(decision)

@router.get("/automation/stats")
async def get_automation_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get automation statistics."""
    engine = AutomatedDecisionEngine(db)
    return await engine.get_automation_stats()

@router.get("/automation/pending")
async def get_pending_automations(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get decisions pending automation."""
    engine = AutomatedDecisionEngine(db)
    return await engine.get_pending_automations()
