"""
Proactive Suggestions Endpoint - Get proactive suggestions for users
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.proactive.suggester import ProactiveSuggester

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/proactive", tags=["proactive"])


class SuggestionResponse(BaseModel):
    suggestions: list
    count: int
    timestamp: str


@router.get("/suggestions/{user_id}")
async def get_suggestions(
    user_id: int,
    query: Optional[str] = Query(None, description="Current user query"),
    context: Optional[str] = Query(None, description="Context JSON string")
) -> SuggestionResponse:
    """
    Get proactive suggestions for a user.
    """
    suggester = ProactiveSuggester()
    
    try:
        context_dict = {}
        if context:
            import json
            context_dict = json.loads(context)
        
        suggestions = await suggester.get_suggestions(
            user_id=user_id,
            context=context_dict,
            query=query
        )
        
        return SuggestionResponse(
            suggestions=[
                {
                    "id": s.id,
                    "type": s.type,
                    "confidence": s.confidence,
                    "title": s.title,
                    "description": s.description,
                    "action": s.action,
                    "metadata": s.metadata
                }
                for s in suggestions
            ],
            count=len(suggestions),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/{suggestion_id}/dismiss")
async def dismiss_suggestion(suggestion_id: str, user_id: int):
    """
    Dismiss a suggestion.
    """
    return {
        "success": True,
        "suggestion_id": suggestion_id,
        "dismissed": True
    }


@router.post("/suggestions/{suggestion_id}/execute")
async def execute_suggestion(suggestion_id: str, user_id: int):
    """
    Execute a suggestion's action.
    """
    return {
        "success": True,
        "suggestion_id": suggestion_id,
        "executed": True
    }
