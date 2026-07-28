"""
Governance API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import require_admin
from app.services.governance.audit_service import AuditService
from app.services.governance.explainability import ExplainabilityEngine

router = APIRouter(prefix="/governance", tags=["governance"])

@router.get("/audit/{decision_id}")
async def get_audit_trail(
    decision_id: str,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get audit trail for a decision."""
    service = AuditService(lambda: db)
    trail = await service.get_audit_trail(decision_id)
    
    if not trail:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    return trail

@router.get("/audit/user/{user_id}")
async def get_user_audit_trail(
    user_id: int,
    limit: int = 50,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get audit trail for a user."""
    service = AuditService(lambda: db)
    trails = await service.get_audit_trail_for_user(user_id, limit)
    return {"total": len(trails), "trails": trails}

@router.get("/explain/{decision_id}")
async def explain_decision(
    decision_id: str,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get explanation for a decision."""
    engine = ExplainabilityEngine(lambda: db)
    explanation = await engine.explain_decision(decision_id)
    
    if "error" in explanation:
        raise HTTPException(status_code=404, detail=explanation["error"])
    
    return explanation
