from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.nlq_service import NLQService

router = APIRouter(prefix="/api/v1/nlq", tags=["nlq"])


class NLQRequest(BaseModel):
    query: str
    context: dict = None


@router.post("/query")
async def natural_language_query(
    request: NLQRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute a natural language query over intelligence data."""
    service = NLQService(db)
    return await service.query(request.query, current_user, request.context)


@router.get("/suggestions")
async def get_query_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get suggested natural language queries."""
    return {
        "suggestions": [
            {"text": "Show me all security decisions from last week", "category": "Security"},
            {"text": "Why was this decision made?", "category": "Explanation"},
            {"text": "What patterns are emerging in my decisions?", "category": "Patterns"},
            {"text": "Summarize my recent compliance decisions", "category": "Summary"},
            {"text": "Find high confidence decisions about contracts", "category": "Contracts"}
        ]
    }
