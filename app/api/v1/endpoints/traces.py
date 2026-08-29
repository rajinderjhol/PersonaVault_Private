from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List
from app.db.session import get_db
from app.services.trace_service import TraceService
from app.models.decision_trace import DecisionTrace

router = APIRouter(prefix="/api/v1/traces", tags=["traces"])

@router.get("/recent")
async def get_recent_traces(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get the most recent decision traces"""
    service = TraceService(db)
    traces = await service.get_recent_traces(limit)
    return [t.to_dict() for t in traces]

@router.get("/session/{session_id}")
async def get_session_traces(
    session_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """Get all traces for a session"""
    service = TraceService(db)
    traces = await service.get_session_traces(session_id)
    return [t.to_dict() for t in traces]

@router.get("/{trace_id}")
async def get_trace(
    trace_id: UUID, 
    db: AsyncSession = Depends(get_db)
):
    """Retrieve a full decision trace with provenance"""
    service = TraceService(db)
    trace = await service.get_full_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace.to_dict()

@router.post("/{trace_id}/crystallize")
async def mark_crystallized(
    trace_id: UUID, 
    db: AsyncSession = Depends(get_db)
):
    """Mark a trace as crystallized (Layer 3 memory)"""
    service = TraceService(db)
    trace = await service.get_full_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    trace.is_crystallized = True
    await db.commit()
    return {"status": "crystallized", "trace_id": str(trace_id)}