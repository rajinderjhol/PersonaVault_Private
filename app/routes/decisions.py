"""
Decision Routes - API endpoints for decision traces
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from typing import Optional
from datetime import datetime

from app.services.trace_service import get_trace_service, TraceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/decisions", tags=["decisions"])


@router.get("/{decision_id}/trace")
async def get_trace(decision_id: str, service: TraceService = Depends(get_trace_service)):
    """Get the full decision trace for a decision ID"""
    trace = service.get_trace(decision_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {decision_id} not found")
    
    return {
        "decision_id": trace.decision_id,
        "timestamp": trace.timestamp,
        "query": trace.query,
        "response": trace.response,
        "trace": trace.trace,
        "explanation": trace.explanation,
        "pack": {
            "name": trace.pack_name,
            "version": trace.pack_version
        },
        "latency_ms": trace.latency_ms
    }


@router.get("/{decision_id}/export")
async def export_trace(
    decision_id: str, 
    format: str = Query("json", enum=["json", "pretty"]),
    service: TraceService = Depends(get_trace_service)
):
    """Export a trace in various formats"""
    exported = service.export_trace(decision_id, format=format)
    if not exported:
        raise HTTPException(status_code=404, detail=f"Trace {decision_id} not found")
    
    return Response(
        content=exported,
        media_type="application/json" if format == "json" else "text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="trace_{decision_id}.{format}"'
        }
    )


@router.get("/{decision_id}/verify")
async def verify_trace(
    decision_id: str,
    service: TraceService = Depends(get_trace_service)
):
    """Verify a trace's integrity and reproducibility"""
    result = service.verify_trace(decision_id)
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result


@router.get("/recent")
async def get_recent_traces(
    limit: int = Query(10, ge=1, le=50),
    service: TraceService = Depends(get_trace_service)
):
    """Get recent decision traces"""
    traces = service.get_recent_traces(limit)
    return {
        "count": len(traces),
        "traces": [
            {
                "decision_id": t.decision_id,
                "timestamp": t.timestamp,
                "query": t.query,
                "response": t.response[:100] + "..." if len(t.response) > 100 else t.response,
                "pack_name": t.pack_name,
                "latency_ms": t.latency_ms
            }
            for t in traces
        ]
    }


@router.post("/{decision_id}/replay")
async def replay_decision(
    decision_id: str,
    service: TraceService = Depends(get_trace_service)
):
    """Replay a decision (requires orchestrator integration)"""
    # This would need to call the orchestrator with the same inputs
    # For now, return a placeholder
    trace = service.get_trace(decision_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {decision_id} not found")
    
    return {
        "status": "replay_available",
        "original_trace": trace.decision_id,
        "message": "Replay functionality requires orchestrator integration",
        "query": trace.query
    }
