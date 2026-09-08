"""
Intelligence Source Control - V2 API Endpoint (SQLite-Backed)
Manages devices/IoT/agents as intelligence sources with dynamic trust scoring.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.intelligence_source import IntelligenceSource as SourceModel
from app.models.user import User
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/intelligence-sources", tags=["Intelligence Sources"])

# ============================================================
# Pydantic Models
# ============================================================

class TrustScoreHistory(BaseModel):
    timestamp: datetime
    score: float
    reason: str

class ContributionMetrics(BaseModel):
    patterns_crystallized: int = 0
    reasoning_steps_validated: int = 0
    memory_matches_contributed: int = 0
    decision_traces_triggered: int = 0
    events_ingested: int = 0

class IntelligenceSourceResponse(BaseModel):
    id: str
    name: str
    type: str
    trust_score: float
    trust_level: str
    trust_history: List[TrustScoreHistory]
    contribution_metrics: ContributionMetrics
    memory_access: List[str]
    status: str
    last_contribution: Optional[datetime]
    registered_at: datetime
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)

class SourceRegistrationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., pattern="^(endpoint|iot|agent|behavior_pack)$")
    initial_trust_level: str = Field("BASIC", pattern="^(FULL|HIGH|MEDIUM|BASIC|UNTRUSTED)$")
    memory_access: List[str] = ["gas"]
    purpose: Optional[str] = None

class SourceUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    trust_level: Optional[str] = Field(None, pattern="^(FULL|HIGH|MEDIUM|BASIC|UNTRUSTED)$")
    memory_access: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(active|idle|degraded|offline)$")
    metadata: Optional[Dict[str, Any]] = None

# ============================================================
# Constants
# ============================================================

TRUST_LEVEL_MAP = {
    "FULL": 0.95,
    "HIGH": 0.85,
    "MEDIUM": 0.70,
    "BASIC": 0.55,
    "UNTRUSTED": 0.35,
}

# ============================================================
# Helper Functions
# ============================================================

def model_to_response(model: SourceModel) -> IntelligenceSourceResponse:
    """Convert DB model to response schema."""
    return IntelligenceSourceResponse(
        id=model.id,
        name=model.name,
        type=model.type,
        trust_score=float(model.trust_score) if model.trust_score else 0.50,
        trust_level=model.trust_level or "BASIC",
        trust_history=[TrustScoreHistory(**h) if isinstance(h, dict) else h for h in (model.trust_history or [])],
        contribution_metrics=ContributionMetrics(**(model.contribution_metrics or {})),
        memory_access=model.memory_access or ["gas"],
        status=model.status or "active",
        last_contribution=model.last_contribution,
        registered_at=model.registered_at or datetime.utcnow(),
        extra_metadata=model.extra_metadata or {},
    )

def trust_level_to_score(level: str) -> float:
    """Map trust level to numeric score."""
    return TRUST_LEVEL_MAP.get(level, 0.55)

# ============================================================
# Live Feed (In-memory for SQLite development)
# ============================================================

_live_feed: List[Dict[str, Any]] = []
_MAX_FEED_SIZE = 500

async def log_live_feed_event(
    source_id: str,
    source_name: str,
    event_type: str,
    message: str,
    details: Dict[str, Any] = None,
):
    """Log an event to the live feed."""
    event = {
        "source_id": source_id,
        "source_name": source_name,
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "message": message,
        "details": details or {},
    }
    _live_feed.insert(0, event)
    # Keep only last 500 events
    if len(_live_feed) > _MAX_FEED_SIZE:
        _live_feed.pop()

# ============================================================
# API Endpoints
# ============================================================

@router.get("/live-feed", response_model=List[Dict[str, Any]])
async def get_live_feed(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """Get recent live feed events."""
    return _live_feed[:limit]


@router.get("/trust-levels", response_model=Dict[str, Dict])
async def get_trust_levels():
    """Get available trust levels and their configuration."""
    return {
        "FULL": {
            "value": 0.95,
            "label": "Full Trust",
            "access": ["gas", "liquid", "ice", "crystallized"],
            "color": "#00b894"
        },
        "HIGH": {
            "value": 0.85,
            "label": "High Trust",
            "access": ["gas", "liquid", "ice"],
            "color": "#00b894"
        },
        "MEDIUM": {
            "value": 0.70,
            "label": "Medium Trust",
            "access": ["gas", "liquid"],
            "color": "#fdcb6e"
        },
        "BASIC": {
            "value": 0.55,
            "label": "Basic Trust",
            "access": ["gas"],
            "color": "#fdcb6e"
        },
        "UNTRUSTED": {
            "value": 0.35,
            "label": "Untrusted",
            "access": [],
            "color": "#e17055"
        },
    }


@router.get("/stats", response_model=Dict[str, Any])
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aggregated statistics about intelligence sources."""
    # Count total sources
    total_query = select(func.count(SourceModel.id)).where(SourceModel.user_id == current_user.id)
    total_result = await db.execute(total_query)
    total_count = total_result.scalar() or 0
    
    if total_count == 0:
        return {
            "active_sources": 0,
            "total_sources": 0,
            "average_trust_score": 0,
            "total_contributions": 0,
            "total_ingestions": 0,
        }
    
    # Count active sources
    active_query = select(func.count(SourceModel.id)).where(
        SourceModel.user_id == current_user.id,
        SourceModel.status == "active"
    )
    active_result = await db.execute(active_query)
    active_count = active_result.scalar() or 0
    
    # Get all sources for avg trust and metrics
    stmt = select(SourceModel).where(SourceModel.user_id == current_user.id)
    result = await db.execute(stmt)
    sources = result.scalars().all()
    
    avg_trust = sum(float(s.trust_score) for s in sources) / len(sources) if sources else 0.0
    total_contributions = sum(
        (s.contribution_metrics or {}).get("patterns_crystallized", 0) +
        (s.contribution_metrics or {}).get("reasoning_steps_validated", 0)
        for s in sources
    )
    total_ingestions = sum(
        (s.contribution_metrics or {}).get("events_ingested", 0)
        for s in sources
    )
    
    return {
        "active_sources": active_count,
        "total_sources": total_count,
        "average_trust_score": round(avg_trust, 2),
        "total_contributions": total_contributions,
        "total_ingestions": total_ingestions,
    }


@router.get("/", response_model=List[IntelligenceSourceResponse])
async def list_sources(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = Query(None, description="Filter by status (active|idle|degraded|offline)"),
    source_type: Optional[str] = Query(None, alias="type", description="Filter by type (endpoint|iot|agent|behavior_pack)"),
    min_trust: Optional[float] = Query(None, description="Minimum trust score"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """List all intelligence sources for the current user."""
    query = select(SourceModel).where(SourceModel.user_id == current_user.id)
    
    if status:
        query = query.where(SourceModel.status == status)
    if source_type:
        query = query.where(SourceModel.type == source_type)
    if min_trust is not None:
        query = query.where(SourceModel.trust_score >= min_trust)
    
    result = await db.execute(query.order_by(SourceModel.trust_score.desc()).offset(offset).limit(limit))
    results = result.scalars().all()
    return [model_to_response(r) for r in results]


@router.get("/{source_id}", response_model=IntelligenceSourceResponse)
async def get_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed information about a specific intelligence source."""
    stmt = select(SourceModel).where(
        SourceModel.id == source_id,
        SourceModel.user_id == current_user.id
    )
    result = await db.execute(stmt)
    source = result.scalars().first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return model_to_response(source)


@router.post("/", response_model=IntelligenceSourceResponse, status_code=201)
async def register_source(
    request: SourceRegistrationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a new intelligence source."""
    source_id = f"src-{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow()
    
    initial_score = trust_level_to_score(request.initial_trust_level)
    
    source = SourceModel(
        id=source_id,
        user_id=current_user.id,
        name=request.name,
        type=request.type,
        trust_score=initial_score,
        trust_level=request.initial_trust_level,
        trust_history=[{
            "timestamp": now.isoformat(),
            "score": initial_score,
            "reason": "Initial registration"
        }],
        contribution_metrics={
            "patterns_crystallized": 0,
            "reasoning_steps_validated": 0,
            "memory_matches_contributed": 0,
            "decision_traces_triggered": 0,
            "events_ingested": 0,
        },
        memory_access=request.memory_access or ["gas"],
        status="active",
        registered_at=now,
        extra_metadata={"purpose": request.purpose or "No purpose specified"},
        created_at=now,
        updated_at=now,
    )
    
    db.add(source)
    await db.commit()
    await db.refresh(source)
    
    # Log to live feed
    background_tasks.add_task(
        log_live_feed_event,
        source_id=source_id,
        source_name=request.name,
        event_type="registration",
        message=f"New source registered: {request.name}",
        details={"trust_level": request.initial_trust_level}
    )
    
    return model_to_response(source)


@router.patch("/{source_id}", response_model=IntelligenceSourceResponse)
async def update_source(
    source_id: str,
    request: SourceUpdateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing intelligence source."""
    stmt = select(SourceModel).where(
        SourceModel.id == source_id,
        SourceModel.user_id == current_user.id
    )
    result = await db.execute(stmt)
    source = result.scalars().first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    if request.name is not None:
        source.name = request.name
    
    if request.trust_level is not None:
        old_trust = source.trust_level
        source.trust_level = request.trust_level
        source.trust_score = trust_level_to_score(request.trust_level)
        # Append to history
        history = source.trust_history or []
        history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "score": float(source.trust_score),
            "reason": f"Trust level changed from {old_trust} to {request.trust_level}"
        })
        source.trust_history = history
    
    if request.memory_access is not None:
        source.memory_access = request.memory_access
    
    if request.status is not None:
        source.status = request.status
    
    if request.metadata is not None:
        source.extra_metadata = request.metadata
    
    source.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(source)
    
    # Log to live feed
    background_tasks.add_task(
        log_live_feed_event,
        source_id=source_id,
        source_name=source.name,
        event_type="update",
        message=f"Source updated: {source.name}",
        details={"changes": request.dict(exclude_unset=True)}
    )
    
    return model_to_response(source)


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an intelligence source."""
    stmt = select(SourceModel).where(
        SourceModel.id == source_id,
        SourceModel.user_id == current_user.id
    )
    result = await db.execute(stmt)
    source = result.scalars().first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    await db.delete(source)
    await db.commit()
    return None


@router.post("/{source_id}/recompute-trust")
async def recompute_trust(
    source_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger trust score recomputation based on contribution quality."""
    stmt = select(SourceModel).where(
        SourceModel.id == source_id,
        SourceModel.user_id == current_user.id
    )
    result = await db.execute(stmt)
    source = result.scalars().first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    metrics = source.contribution_metrics or {}
    base_score = 0.35
    
    if metrics.get("patterns_crystallized", 0) > 0:
        base_score += 0.15
    if metrics.get("reasoning_steps_validated", 0) > 50:
        base_score += 0.15
    if metrics.get("events_ingested", 0) > 100:
        base_score += 0.10
    
    new_score = min(base_score, 0.95)
    old_score = float(source.trust_score) if source.trust_score else 0.35
    
    source.trust_score = new_score
    history = source.trust_history or []
    history.append({
        "timestamp": datetime.utcnow().isoformat(),
        "score": new_score,
        "reason": f"Recomputed based on contributions (was {old_score:.2f})"
    })
    source.trust_history = history
    source.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(source)
    
    # Log to live feed
    background_tasks.add_task(
        log_live_feed_event,
        source_id=source_id,
        source_name=source.name,
        event_type="trust_change",
        message=f"Trust score updated: {old_score:.2f} \u2192 {new_score:.2f}",
        details={"old_score": old_score, "new_score": new_score}
    )
    
    return {"source_id": source_id, "old_score": old_score, "new_score": new_score}


@router.post("/{source_id}/ingest")
async def ingest_data(
    source_id: str,
    data_type: str = Query(..., description="Type of data being ingested"),
    size_bytes: int = Query(..., ge=1, description="Size of data in bytes"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Simulate data ingestion from a source."""
    stmt = select(SourceModel).where(
        SourceModel.id == source_id,
        SourceModel.user_id == current_user.id
    )
    result = await db.execute(stmt)
    source = result.scalars().first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    trust_score = float(source.trust_score) if source.trust_score else 0.50
    
    # Determine if data should be accepted based on trust
    accepted = trust_score >= 0.40
    memory_layer = "gas"
    reason = None
    
    if trust_score >= 0.85:
        memory_layer = "ice"
    elif trust_score >= 0.70:
        memory_layer = "liquid"
    elif trust_score >= 0.40:
        memory_layer = "gas"
    else:
        accepted = False
        reason = f"Trust score too low ({trust_score:.2f})"
    
    # Check memory access
    memory_access = source.memory_access or ["gas"]
    if accepted and memory_layer not in memory_access:
        accepted = False
        reason = f"Source does not have access to {memory_layer} layer"
    
    event = {
        "source_id": source_id,
        "source_name": source.name,
        "data_type": data_type,
        "size_bytes": size_bytes,
        "memory_layer": memory_layer,
        "accepted": accepted,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Update contribution metrics
    if accepted:
        metrics = source.contribution_metrics or {}
        metrics["events_ingested"] = metrics.get("events_ingested", 0) + 1
        source.contribution_metrics = metrics
        source.last_contribution = datetime.utcnow()
        source.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(source)
        
        await log_live_feed_event(
            source_id=source_id,
            source_name=source.name,
            event_type="ingestion",
            message=f"Ingested {data_type} ({size_bytes} bytes) \u2192 {memory_layer} layer",
            details={"data_type": data_type, "size_bytes": size_bytes, "memory_layer": memory_layer}
        )
    else:
        await log_live_feed_event(
            source_id=source_id,
            source_name=source.name,
            event_type="alert",
            message=f"\u274c Ingestion rejected: {reason}",
            details={"data_type": data_type, "reason": reason}
        )
    
    return event
