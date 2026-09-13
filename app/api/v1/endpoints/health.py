"""
Decision Health API - Aggregated system health metrics
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.db.session import get_db
from app.models.decision_trace import DecisionTrace
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.intelligence_gateway import gateway
import logging

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/decision")
async def get_decision_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get aggregated decision health score.
    """
    try:
        # 1. Calculate confidence health
        confidence_health = await _get_confidence_health(db)
        
        # 2. Calculate crystallization health
        crystallization_health = await _get_crystallization_health(db)
        
        # 3. Calculate trace health (volume and quality)
        trace_health = await _get_trace_health(db)
        
        # 4. Calculate system health (providers, latency)
        system_health = await _get_system_health()
        
        # Aggregate overall score
        components = [
            confidence_health,
            crystallization_health,
            trace_health,
            system_health
        ]
        
        overall_score = sum(c['score'] for c in components) / len(components)
        
        return {
            "overall": {
                "score": round(overall_score, 2),
                "status": _get_status(overall_score),
                "timestamp": datetime.utcnow().isoformat()
            },
            "components": {
                "confidence": confidence_health,
                "crystallization": crystallization_health,
                "traces": trace_health,
                "system": system_health
            },
            "metrics": await _get_detailed_metrics(db)
        }
        
    except Exception as e:
        logger.error(f"Failed to get decision health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get decision health")


async def _get_confidence_health(db: AsyncSession) -> Dict[str, Any]:
    """Calculate confidence-based health score."""
    try:
        # Get average confidence
        result = await db.execute(
            select(func.avg(DecisionTrace.confidence_score))
            .where(DecisionTrace.confidence_score.isnot(None))
        )
        avg_confidence = result.scalar() or 0.0
        
        # Get confidence trend (last 30 days vs previous)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        sixty_days_ago = datetime.utcnow() - timedelta(days=60)
        
        recent_result = await db.execute(
            select(func.avg(DecisionTrace.confidence_score))
            .where(DecisionTrace.timestamp >= thirty_days_ago)
            .where(DecisionTrace.confidence_score.isnot(None))
        )
        recent_avg = recent_result.scalar() or 0.0
        
        previous_result = await db.execute(
            select(func.avg(DecisionTrace.confidence_score))
            .where(DecisionTrace.timestamp.between(sixty_days_ago, thirty_days_ago))
            .where(DecisionTrace.confidence_score.isnot(None))
        )
        previous_avg = previous_result.scalar() or 0.0
        
        trend = "stable"
        if recent_avg > previous_avg + 0.05:
            trend = "improving"
        elif recent_avg < previous_avg - 0.05:
            trend = "declining"
        
        return {
            "score": round(avg_confidence * 100, 1),
            "status": "healthy" if avg_confidence > 0.7 else "warning" if avg_confidence > 0.5 else "critical",
            "trend": trend,
            "details": {
                "average": round(avg_confidence, 3),
                "recent": round(recent_avg, 3),
                "previous": round(previous_avg, 3),
                "sample_count": await _get_confidence_sample_count(db)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get confidence health: {e}")
        return {"score": 0, "status": "unknown", "trend": "unknown", "details": {}}


async def _get_crystallization_health(db: AsyncSession) -> Dict[str, Any]:
    """Calculate crystallization-based health score."""
    try:
        # Count crystallized patterns
        total_result = await db.execute(
            select(func.count()).select_from(DecisionTrace)
        )
        total = total_result.scalar() or 1
        
        crystallized_result = await db.execute(
            select(func.count()).select_from(DecisionTrace)
            .where(DecisionTrace.is_crystallized == True)
        )
        crystallized = crystallized_result.scalar() or 0
        
        # Crystallization rate
        rate = crystallized / total if total > 0 else 0
        
        # Score based on rate (target > 30%)
        score = min(rate * 100, 100)
        
        # Trend: compare to 30 days ago
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_result = await db.execute(
            select(func.count()).select_from(DecisionTrace)
            .where(DecisionTrace.timestamp >= thirty_days_ago)
            .where(DecisionTrace.is_crystallized == True)
        )
        recent_crystallized = recent_result.scalar() or 0
        
        recent_total_result = await db.execute(
            select(func.count()).select_from(DecisionTrace)
            .where(DecisionTrace.timestamp >= thirty_days_ago)
        )
        recent_total = recent_total_result.scalar() or 1
        
        recent_rate = recent_crystallized / recent_total if recent_total > 0 else 0
        
        trend = "improving" if recent_rate > rate else "stable" if recent_rate == rate else "declining"
        
        return {
            "score": round(score, 1),
            "status": "healthy" if score > 30 else "warning" if score > 10 else "critical",
            "trend": trend,
            "details": {
                "crystallized": crystallized,
                "total": total,
                "rate": round(rate * 100, 1),
                "recent_rate": round(recent_rate * 100, 1)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get crystallization health: {e}")
        return {"score": 0, "status": "unknown", "trend": "unknown", "details": {}}


async def _get_trace_health(db: AsyncSession) -> Dict[str, Any]:
    """Calculate trace-based health score."""
    try:
        # Get total traces
        result = await db.execute(select(func.count()).select_from(DecisionTrace))
        total = result.scalar() or 0
        
        # Get traces in last 24 hours
        day_ago = datetime.utcnow() - timedelta(days=1)
        daily_result = await db.execute(
            select(func.count()).select_from(DecisionTrace)
            .where(DecisionTrace.timestamp >= day_ago)
        )
        daily = daily_result.scalar() or 0
        
        # Score based on daily activity (target > 10 per day)
        activity_score = min((daily / 10) * 100, 100) if total > 0 else 0
        
        # Quality: check if traces have confidence scores
        quality_result = await db.execute(
            select(func.avg(DecisionTrace.confidence_score))
            .where(DecisionTrace.confidence_score.isnot(None))
        )
        avg_confidence = quality_result.scalar() or 0.0
        
        # Combined score
        score = (activity_score * 0.6) + (avg_confidence * 40)
        
        # Trend: compare daily activity to weekly average
        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_result = await db.execute(
            select(func.count()).select_from(DecisionTrace)
            .where(DecisionTrace.timestamp >= week_ago)
        )
        weekly = (weekly_result.scalar() or 0) / 7
        
        trend = "improving" if daily > weekly * 1.1 else "stable" if daily >= weekly * 0.9 else "declining"
        
        return {
            "score": round(min(score, 100), 1),
            "status": "healthy" if score > 60 else "warning" if score > 30 else "critical",
            "trend": trend,
            "details": {
                "total": total,
                "daily": daily,
                "weekly_average": round(weekly, 1),
                "avg_confidence": round(avg_confidence, 3)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get trace health: {e}")
        return {"score": 0, "status": "unknown", "trend": "unknown", "details": {}}


async def _get_system_health() -> Dict[str, Any]:
    """Calculate system health score."""
    try:
        # Check provider status
        providers = gateway.get_providers()
        active_providers = [p for p in providers.values() if p.get("enabled")]
        total_providers = len(providers)
        
        provider_score = (len(active_providers) / total_providers * 100) if total_providers > 0 else 0
        
        return {
            "score": round(provider_score, 1),
            "status": "healthy" if provider_score > 50 else "warning" if provider_score > 25 else "critical",
            "trend": "stable",
            "details": {
                "active_providers": len(active_providers),
                "total_providers": total_providers,
                "providers": list(providers.keys())
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        return {"score": 0, "status": "unknown", "trend": "unknown", "details": {}}


def _get_status(score: float) -> str:
    """Get status based on score."""
    if score >= 70:
        return "healthy"
    elif score >= 40:
        return "warning"
    else:
        return "critical"


async def _get_confidence_sample_count(db: AsyncSession) -> int:
    """Get count of traces with confidence scores."""
    result = await db.execute(
        select(func.count()).select_from(DecisionTrace)
        .where(DecisionTrace.confidence_score.isnot(None))
    )
    return result.scalar() or 0


async def _get_detailed_metrics(db: AsyncSession) -> Dict[str, Any]:
    """Get detailed metrics for the health report."""
    try:
        # Count by step
        step_result = await db.execute(
            select(DecisionTrace.step, func.count())
            .group_by(DecisionTrace.step)
        )
        step_counts = step_result.all()
        
        return {
            "step_distribution": {step.value if hasattr(step, 'value') else str(step): count for step, count in step_counts},
            "crystallization_rate": await _get_crystallization_health(db)
        }
    except Exception as e:
        logger.error(f"Failed to get detailed metrics: {e}")
        return {}
