from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.onboarding_service import OnboardingService, ConciergeAgent

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])


@router.get("/plan")
async def get_onboarding_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get personalized onboarding plan for the current user."""
    service = OnboardingService(db)
    return await service.get_onboarding_plan(current_user)


@router.get("/greeting")
async def get_concierge_greeting(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get AI Concierge greeting message."""
    agent = ConciergeAgent(db)
    return {
        "greeting": await agent.greet_user(current_user),
        "suggestion": await agent.suggest_next_action(current_user)
    }


@router.post("/complete-step")
async def complete_onboarding_step(
    step: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark an onboarding step as complete."""
    # In production, store this in User preferences or onboarding tracking
    return {
        "status": "success",
        "message": f"Step '{step}' marked as complete",
        "next_steps": [
            "Configure your dashboard",
            "Explore your domain packs",
            "Try the Cognitive Lab"
        ]
    }
