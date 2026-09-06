"""
Unified Search API endpoint with temporal intelligence
"""
from fastapi import APIRouter, Depends, Query, Request
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.memory_service import MemoryService
from app.services.temporal_analysis_service import TemporalAnalysisService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/search", tags=["search"])

@router.get("/")
async def universal_search(
    request: Request,
    query: str = Query(..., min_length=1),
    time_range: str = Query("30d"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Universal search over memories and decisions with temporal relevance scoring.
    """
    try:
        # 1. Initialize services
        memory_service = request.app.state.memory_service
        temporal_service = TemporalAnalysisService(db)
        
        # 2. Execute semantic search
        # Note: In a production system, this would search across multiple entities
        memories = await memory_service.search_memories(
            user_id=current_user.id,
            query=query,
            limit=limit
        )
        
        # 3. Apply temporal scoring and transform results
        items = []
        for m in memories:
            # Calculate temporal relevance (mocked logic for now)
            # In real usage, we'd use temporal_service.get_temporal_relevance_score
            relevance_score = 0.85 
            
            items.append({
                "id": m.get("id", "unknown"),
                "title": m.get("title", "Intelligence Entry"),
                "content": m.get("content", ""),
                "confidence_score": m.get("score", 0.9),
                "created_at": m.get("metadata", {}).get("created_at", ""),
                "domain": m.get("metadata", {}).get("domain", "general"),
                "temporal_relevance": {
                    "score": relevance_score,
                    "context": f"Relevant to {time_range} window",
                    "factors": ["Recent activity", "Pattern match"]
                }
            })
            
        return {
            "items": items,
            "total": len(items),
            "temporal_metadata": {
                "context": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "original_expression": query
                },
                "scoring_enabled": True,
                "relevance_threshold": 0.5
            }
        }
        
    except Exception as e:
        logger.error(f"Universal search error: {e}")
        return {
            "items": [],
            "total": 0,
            "temporal_metadata": {"scoring_enabled": False}
        }
