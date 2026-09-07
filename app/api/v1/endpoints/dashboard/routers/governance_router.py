from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import logging

from app.api.v1.endpoints.auth import get_current_user_logic as get_current_user
from app.core.dependencies import require_admin
from app.db.session import get_db
from app.models import PendingAction, EpisodicEntry, SystemConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["admin"])

# ============ HITL (Human-In-The-Loop) ============

@router.get("/hitl/pending")
async def list_pending_hitl(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        await get_current_user(request, db=db)
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/api/v1/auth/login", status_code=303)
        raise e
        
    stmt = select(PendingAction).where(PendingAction.status == "pending").order_by(PendingAction.created_at.desc())
    results = (await db.execute(stmt)).scalars().all()
    return [{"id": p.id, "agent_type": p.agent_type, "query": p.query, "timestamp": p.created_at.isoformat()} for p in results]


@router.post("/hitl/approve-all")
async def approve_all_hitl(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(PendingAction).where(PendingAction.status == "pending")
    actions = (await db.execute(stmt)).scalars().all()
    for action in actions:
        action.status = "approved"
        action.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "success", "count": len(actions)}


@router.post("/hitl/deny-all")
async def deny_all_hitl(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(PendingAction).where(PendingAction.status == "pending")
    actions = (await db.execute(stmt)).scalars().all()
    for action in actions:
        action.status = "rejected"
        action.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "success", "count": len(actions)}


# ============ GOVERNANCE ============

@router.get("/governance/logs")
async def get_governance_logs(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        await get_current_user(request, db=db)
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/api/v1/auth/login", status_code=303)
        raise e
        
    stmt = select(EpisodicEntry).order_by(EpisodicEntry.timestamp.desc()).limit(20)
    results = (await db.execute(stmt)).scalars().all()
    return {"logs": [{"id": e.id, "query": e.query or "No query", "receipt": e.governance_receipt_id or "local", "timestamp": e.timestamp.isoformat(), "hitl": e.hitl_approved} for e in results]}


@router.post("/governance/toggle-offline")
async def toggle_verilink_offline(request: Request, user_id: int = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator missing")
    new_state = not getattr(orchestrator, "offline_mode", False)

    stmt = select(SystemConfig).where(SystemConfig.key == "verilink_offline_mode")
    config = (await db.execute(stmt)).scalars().first()
    
    val_str = "true" if new_state else "false"
    
    if not config:
        db.add(SystemConfig(key="verilink_offline_mode", value=val_str))
    else:
        config.value = val_str
    
    await db.commit()

    orchestrator.offline_mode = new_state

    if new_state:
        orchestrator.governance = None
        orchestrator.governance_status = "manual_offline"
        logger.info("Admin manually suppressed VeriLink connection.")
    else:
        try:
            from verilink_plugin import VeriLinkGovernancePlugin
            orchestrator.governance = VeriLinkGovernancePlugin()
            orchestrator.governance_status = "active"
            logger.info("Admin resumed VeriLink connection attempts.")
        except Exception as e:
            orchestrator.governance = None
            orchestrator.governance_status = "offline_fail_soft"
            logger.warning(f"VeriLink resume failed: {e}")

    return {"status": "success", "offline_mode": new_state}
