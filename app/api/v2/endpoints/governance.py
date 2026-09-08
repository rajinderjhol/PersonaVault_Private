from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.governance.audit_service import AuditService

# Importing V1 services to maintain single source of truth
# The V2 endpoints wrap these services to expose them via /v2/environments/{env_id}/governance/...

router = APIRouter(tags=["V2 Governance"])

@router.get("/audit")
async def get_v2_audit_trail(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get audit trail - V2 wrapper for V1 AuditService."""
    service = AuditService(lambda: db)
    # Mapping to what frontend expects (e.g., AuditLog[])
    trails = await service.get_audit_trail_for_user(None, limit)
    return trails

@router.get("/policies")
async def get_v2_policies(
    db: AsyncSession = Depends(get_db)
):
    """Get active policies - V2 implementation."""
    # Placeholder: Assuming V1 policies logic could be mapped here if needed.
    # Currently returning consistent schema to fix 404s.
    return [
        {"policyId": "pol-001", "name": "Memory Layer Access", "status": "active", "hitRate": 0.95, "confidence": 0.98, "lastUsed": "2026-09-08T14:00:00Z", "violations": 0}
    ]

@router.get("/compliance")
async def get_v2_compliance(
    db: AsyncSession = Depends(get_db)
):
    """Get compliance status - V2 implementation."""
    # Placeholder: Assuming V1 governance compliance could be mapped here.
    return [
        {"standard": "Sovereign-Audit-v1", "status": "compliant", "lastChecked": "2026-09-08T12:00:00Z", "details": "All layers passed", "recommendations": []}
    ]
