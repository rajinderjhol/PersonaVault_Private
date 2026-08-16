"""
Pattern management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import require_admin
from app.services.self_improving import SelfImprovingIntelligence
from app.models import SemanticPattern
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/patterns", tags=["patterns"])

@router.get("/")
async def get_patterns(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all patterns."""
    service = SelfImprovingIntelligence(db)
    await service.initialize()
    return await service.get_active_patterns()

@router.get("/stats")
async def get_pattern_stats(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get pattern statistics."""
    service = SelfImprovingIntelligence(db)
    await service.initialize()
    return await service.get_learning_stats()

@router.get("/{pattern_type}")
async def get_patterns_by_type(
    pattern_type: str,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get patterns by type."""
    service = SelfImprovingIntelligence(db)
    await service.initialize()
    return await service.get_patterns_by_type(pattern_type)

@router.delete("/{pattern_id}")
async def delete_pattern(
    pattern_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a pattern."""
    stmt = select(SemanticPattern).where(SemanticPattern.id == pattern_id)
    result = await db.execute(stmt)
    pattern = result.scalars().first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    await db.delete(pattern)
    await db.commit()
    return {"status": "deleted"}

@router.post("/{pattern_id}/reinforce")
async def reinforce_pattern(
    pattern_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Manually reinforce a pattern."""
    stmt = select(SemanticPattern).where(SemanticPattern.id == pattern_id)
    result = await db.execute(stmt)
    pattern = result.scalars().first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    pattern.weight += 0.05
    pattern.success_count += 1
    await db.commit()
    return {"status": "reinforced", "new_weight": pattern.weight}
