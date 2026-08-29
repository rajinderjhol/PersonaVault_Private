"""
Decision Routes - API endpoints for decision traces
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from typing import Optional
from uuid import UUID

from app.services.trace_service import get_trace_service, TraceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/decisions", tags=["decisions"])


@router.get("/{decision_id}/trace", response_model=None)
async def get_trace(decision_id: str, service: TraceService = Depends(get_trace_service)):
    """Get the full decision trace for a decision ID"""
    # Assuming UUID is required, convert string
    try:
        uuid_id = UUID(decision_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid decision ID format")
        
    trace = await service.get_full_trace(uuid_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {decision_id} not found")
    
    return trace.to_dict()


@router.get("/{decision_id}/export", response_model=None)
async def export_trace(
    decision_id: str, 
    format: str = Query("json", enum=["json", "pretty"]),
    service: TraceService = Depends(get_trace_service)
):
    """Export a trace in various formats"""
    exported = await service.export_trace(decision_id, format=format)
    if not exported:
        raise HTTPException(status_code=404, detail=f"Trace {decision_id} not found")
    
    return Response(
        content=exported,
        media_type="application/json" if format == "json" else "text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="trace_{decision_id}.{format}"'
        }
    )


@router.get("/{decision_id}/verify", response_model=None)
async def verify_trace(
    decision_id: str,
    service: TraceService = Depends(get_trace_service)
):
    """Verify a trace's integrity and reproducibility"""
    result = await service.verify_trace(decision_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message", "Error verifying trace"))
    
    return result


@router.get("/recent", response_model=None)
async def get_recent_traces(
    limit: int = Query(10, ge=1, le=50),
    service: TraceService = Depends(get_trace_service)
):
    """Get recent decision traces"""
    traces = await service.get_recent_traces(limit)
    return {
        "count": len(traces),
        "traces": [t.to_dict() for t in traces]
    }


@router.post("/{decision_id}/replay", response_model=None)
async def replay_decision(
    decision_id: str,
    service: TraceService = Depends(get_trace_service)
):
    """Replay a decision (requires orchestrator integration)"""
    try:
        uuid_id = UUID(decision_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid decision ID format")

    trace = await service.get_full_trace(uuid_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {decision_id} not found")
    
    return {
        "status": "replay_available",
        "original_trace": str(trace.id),
        "message": "Replay functionality requires orchestrator integration",
        "query": trace.data.get("query", "Unknown query")
    }
