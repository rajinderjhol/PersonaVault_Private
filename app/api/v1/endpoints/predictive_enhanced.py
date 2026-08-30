from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.decision_trace import DecisionTrace
from app.services.predictive_intelligence import PredictiveIntelligenceService

router = APIRouter(prefix="/api/v1/predictive", tags=["predictive"])


@router.get("/predictions")
async def get_predictions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive predictive intelligence for the user."""
    service = PredictiveIntelligenceService(db)
    return await service.get_predictions(current_user)


@router.get("/simulate/{pattern_id}")
async def simulate_pattern(
    pattern_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Simulate outcome of applying a specific pattern."""
    # Get the pattern
    result = await db.execute(
        select(DecisionTrace)
        .where(DecisionTrace.id == pattern_id)
        .where(DecisionTrace.user_id == current_user.id)
    )
    pattern = result.scalar_one_or_none()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    return {
        "pattern": str(pattern.id),
        "domain": pattern.pack_name or "general",
        "confidence": pattern.confidence_score or 0.8,
        "simulation": {
            "success_probability": min((pattern.confidence_score or 0.8) * 1.05, 0.98),
            "risk_level": "low" if (pattern.confidence_score or 0.8) > 0.85 else "medium",
            "expected_impact": {
                "efficiency_gain": round((pattern.confidence_score or 0.8) * 0.3, 2),
                "risk_reduction": round((pattern.confidence_score or 0.8) * 0.2, 2)
            }
        }
    }


@router.get("/trends")
async def get_intelligence_trends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get intelligence trends over time."""
    service = PredictiveIntelligenceService(db)
    return await service._analyze_trends(current_user)


@router.get("/automated-responses")
async def get_automated_responses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get pre-prepared automated responses for expected queries."""
    service = PredictiveIntelligenceService(db)
    return {
        "responses": await service._prepare_automated_responses(current_user)
    }
