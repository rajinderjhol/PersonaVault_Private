"""
Pattern Explorer Endpoints - Browse and interact with crystallized patterns
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from datetime import datetime

from app.services.memory.ice_repository import IceMemoryRepository

router = APIRouter(prefix="/patterns", tags=["patterns"])

@router.get("/")
async def list_patterns(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    domain: Optional[str] = None,
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    search: Optional[str] = None,
    sort_by: str = Query("confidence", pattern="^(confidence|created_at|use_count)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$")
) -> Dict[str, Any]:
    """List crystallized patterns with filtering and sorting."""
    repo = IceMemoryRepository()
    
    patterns = await repo.list_patterns(
        limit=limit,
        offset=offset,
        domain=domain,
        min_confidence=min_confidence,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    total = await repo.count_patterns(
        domain=domain,
        min_confidence=min_confidence,
        search=search
    )
    
    return {
        "patterns": patterns,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }

@router.get("/{pattern_id}")
async def get_pattern(pattern_id: str) -> Dict[str, Any]:
    """Get a specific pattern with full details."""
    repo = IceMemoryRepository()
    pattern = await repo.get_pattern(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return pattern

@router.post("/{pattern_id}/replay")
async def replay_pattern(
    pattern_id: str,
    query: str
) -> Dict[str, Any]:
    """Replay a decision using a specific pattern."""
    repo = IceMemoryRepository()
    pattern = await repo.get_pattern(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    # Re-run the decision with the crystallized pattern
    from app.swarm.orchestrator import MultiAgentOrchestrator
    # Note: Requires a DB session, here mock db_session
    orchestrator = MultiAgentOrchestrator(db_session=None, blackboard=None)
    
    # This assumes reason_with_pattern exists on the orchestrator or service
    result = await orchestrator.reason_with_pattern(
        query=query,
        pattern=pattern
    )
    
    return {
        "pattern_id": pattern_id,
        "query": query,
        "result": result,
        "replayed_at": datetime.now().isoformat()
    }

@router.get("/domains")
async def list_domains() -> List[str]:
    """List all available pattern domains."""
    repo = IceMemoryRepository()
    # Assuming list_domains exists on the repository, fallback to set comprehension if not
    patterns = await repo.list_patterns(limit=200)
    return list(set(p.get("domain", "general") for p in patterns))

@router.get("/statistics")
async def get_pattern_statistics() -> Dict[str, Any]:
    """Get overall pattern statistics."""
    repo = IceMemoryRepository()
    patterns = await repo.list_patterns(limit=200)
    total = len(patterns)
    avg_conf = sum(p.get("confidence", 0) for p in patterns) / total if total > 0 else 0
    return {
        "total_patterns": total,
        "avg_confidence": avg_conf
    }
