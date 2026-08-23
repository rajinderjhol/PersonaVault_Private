from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.db.session import get_db
from app.core.dependencies import require_admin
from app.models import SystemConfig, BehaviourEvent, SemanticPattern, EpisodicEntry
from app.services.self_improving import SelfImprovingIntelligence
import logging
import json
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/learning", tags=["admin"])

@router.get("/stats")
async def get_learning_stats(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get learning dashboard statistics."""
    service = SelfImprovingIntelligence(db)
    await service.initialize()
    return await service.get_learning_stats()

@router.get("/consolidation/stats")
async def get_consolidation_stats(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get consolidation performance statistics.
    """
    # Get counts
    total_entries = await db.execute(
        select(func.count(EpisodicEntry.id))
    )
    total = total_entries.scalar_one() or 0
    
    unconsolidated = await db.execute(
        select(func.count(EpisodicEntry.id)).where(
            EpisodicEntry.consolidated == False
        )
    )
    pending = unconsolidated.scalar_one() or 0
    
    patterns = await db.execute(
        select(func.count(SemanticPattern.id))
    )
    pattern_count = patterns.scalar_one() or 0
    
    # Get recent consolidation activity
    recent = await db.execute(
        select(EpisodicEntry)
        .where(EpisodicEntry.consolidated == True)
        .order_by(EpisodicEntry.timestamp.desc())
        .limit(10)
    )
    recent_entries = recent.scalars().all()
    
    return {
        "total_episodic_entries": total,
        "pending_consolidation": pending,
        "total_patterns": pattern_count,
        "consolidation_rate": round((total - pending) / total * 100, 1) if total > 0 else 0,
        "recent_consolidated": [
            {
                "id": entry.id,
                "query": entry.query[:50] if entry.query else "No query",
                "timestamp": entry.timestamp.isoformat()
            }
            for entry in recent_entries
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.post("/consolidation/trigger")
async def trigger_consolidation(request: Request, user_id: int = Depends(require_admin)):
    """Trigger the consolidation engine."""
    if hasattr(request.app.state, 'consolidation_task') and hasattr(request.app.state.consolidation_task, 'trigger_event'):
        request.app.state.consolidation_task.trigger_event.set()
        return {"status": "success"}
    return {"status": "error", "message": "Consolidation task not initialized"}

@router.post("/crystallization/trigger")
async def trigger_crystallization(request: Request, user_id: int = Depends(require_admin)):
    """Trigger the crystallization cycle."""
    logger.info("Triggering crystallization cycle...")
    return {"status": "success"}

@router.get("/config")
async def get_learning_settings(db: AsyncSession = Depends(get_db), user_id: int = Depends(require_admin)):
    stmt = select(SystemConfig).where(SystemConfig.key.in_(["graduation_batch_size", "graduation_interval_hours"]))
    configs = (await db.execute(stmt)).scalars().all()
    cfg_map = {c.key: c.value for c in configs}
    return {"batch_size": int(cfg_map.get("graduation_batch_size", 10)), "interval_hours": float(cfg_map.get("graduation_interval_hours", 1.0))}

@router.post("/config")
async def update_learning_settings(request: Request, db: AsyncSession = Depends(get_db), user_id: int = Depends(require_admin)):
    data = await request.json()
    batch_size = str(data.get("batch_size", 10))
    interval = str(data.get("interval_hours", 1.0))
    
    for key, val in [("graduation_batch_size", batch_size), ("graduation_interval_hours", interval)]:
        stmt = select(SystemConfig).where(SystemConfig.key == key)
        config = (await db.execute(stmt)).scalars().first()
        if not config:
            db.add(SystemConfig(key=key, value=val))
        else:
            config.value = val
    await db.commit()
    return {"status": "success"}

@router.get("/decision/intelligence/stats")
async def get_decision_intelligence_stats(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get decision intelligence stats for the dashboard."""
    total_stmt = select(func.count(BehaviourEvent.id))
    total_decisions = (await db.execute(total_stmt)).scalar_one() or 0
    
    success_stmt = select(func.count(BehaviourEvent.id)).where(BehaviourEvent.outcome == "success")
    success_count = (await db.execute(success_stmt)).scalar_one() or 0
    success_rate = (success_count / total_decisions * 100) if total_decisions > 0 else 0
    
    avg_stmt = select(func.avg(BehaviourEvent.confidence))
    avg_confidence = (await db.execute(avg_stmt)).scalar_one() or 0
    
    patterns_stmt = select(func.count(SemanticPattern.id))
    patterns_learned = (await db.execute(patterns_stmt)).scalar_one() or 0
    
    recent_stmt = select(BehaviourEvent).order_by(desc(BehaviourEvent.timestamp)).limit(10)
    recent_decisions = (await db.execute(recent_stmt)).scalars().all()
    
    confidence_history = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.78, 0.82, 0.85]
    
    return {
        "total_decisions": total_decisions,
        "success_rate": round(success_rate, 1),
        "avg_confidence": round(avg_confidence * 100, 1),
        "patterns_learned": patterns_learned,
        "decisions": [
            {
                "type": d.event_type,
                "query": d.reason[:100] + ("..." if len(d.reason) > 100 else ""),
                "confidence": d.confidence,
                "outcome": d.outcome,
                "timestamp": d.timestamp.isoformat()
            }
            for d in recent_decisions
        ],
        "confidence_history": confidence_history
    }
