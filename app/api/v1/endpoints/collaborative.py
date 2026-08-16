"""
Collaborative Intelligence API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models import User
from app.services.collaborative import CollaborativeIntelligence
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/collaborative", tags=["collaborative"])

@router.post("/share")
async def share_insight(
    insight: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Share an insight with the team."""
    service = CollaborativeIntelligence(db)
    return await service.share_insight(current_user.id, insight)

@router.post("/transfer")
async def transfer_patterns(
    source_domain: str,
    target_domain: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Transfer learned patterns between domains."""
    service = CollaborativeIntelligence(db)
    return await service.transfer_patterns(source_domain, target_domain)

@router.get("/team/{team_id}/stats")
async def get_team_stats(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get team statistics."""
    service = CollaborativeIntelligence(db)
    return await service.get_team_stats(team_id)
