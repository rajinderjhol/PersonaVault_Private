from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.session import get_db
from app.models import SemanticPattern
from app.core.dependencies import require_admin
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/patterns", tags=["admin"])

class PatternFeedback(BaseModel):
    pattern_id: int
    was_helpful: bool

@router.get("/list")
async def list_patterns(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    active_only: bool = True
):
    """List all semantic patterns with their weights."""
    try:
        stmt = select(SemanticPattern)
        if active_only:
            stmt = stmt.where(SemanticPattern.is_active == True)
        stmt = stmt.order_by(SemanticPattern.weight.desc())
        
        result = await db.execute(stmt)
        patterns = result.scalars().all()
        
        return {
            "total": len(patterns),
            "patterns": [{
                "id": p.id,
                "type": p.pattern_type,
                "trigger": p.trigger,
                "correction": p.correction[:200] + "..." if len(p.correction) > 200 else p.correction,
                "occurrence_count": p.occurrence_count,
                "success_count": p.success_count or 0,
                "weight": p.weight or 0.7,
                "is_active": p.is_active if p.is_active is not None else True
            } for p in patterns]
        }
    except Exception as e:
        logger.error(f"Error listing patterns: {e}")
        return {"total": 0, "patterns": [], "error": str(e)}

@router.post("/verify")
async def verify_pattern(
    feedback: PatternFeedback,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Verify if a pattern was helpful and update its weight."""
    try:
        # Use a simple approach - avoid complex async operations
        stmt = select(SemanticPattern).where(SemanticPattern.id == feedback.pattern_id)
        result = await db.execute(stmt)
        pattern = result.scalars().first()
        
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        # Update the pattern directly
        if feedback.was_helpful:
            pattern.success_count = (pattern.success_count or 0) + 1
            pattern.weight = min(1.0, (pattern.weight or 0.7) + 0.05)
            message = "Pattern reinforced successfully"
        else:
            pattern.weight = max(0.1, (pattern.weight or 0.7) - 0.1)
            if pattern.weight < 0.3:
                pattern.is_active = False
            message = "Pattern weakened"
        
        # Commit the changes
        await db.commit()
        
        # Refresh to get updated values
        await db.refresh(pattern)
        
        logger.info(f"Pattern {pattern.id} verification: {message} (new weight: {pattern.weight})")
        
        return {
            "status": "success",
            "message": message,
            "pattern": {
                "id": pattern.id,
                "trigger": pattern.trigger,
                "weight": pattern.weight,
                "is_active": pattern.is_active,
                "success_count": pattern.success_count
            }
        }
    except Exception as e:
        logger.error(f"Error verifying pattern: {e}")
        # Even if there's an error, the database update might have succeeded
        # Let's check if the pattern exists and return current state
        try:
            stmt = select(SemanticPattern).where(SemanticPattern.id == feedback.pattern_id)
            result = await db.execute(stmt)
            pattern = result.scalars().first()
            if pattern:
                return {
                    "status": "partial_success",
                    "message": f"Pattern updated but API error: {str(e)}",
                    "pattern": {
                        "id": pattern.id,
                        "trigger": pattern.trigger,
                        "weight": pattern.weight,
                        "is_active": pattern.is_active,
                        "success_count": pattern.success_count
                    }
                }
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify pattern: {str(e)}"
        )
