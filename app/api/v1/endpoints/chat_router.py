"""
Chat router - registers endpoints.
"""
from fastapi import APIRouter, Depends, Request
from app.core.dependencies import get_current_user
from app.models import User
from app.api.v1.endpoints.chat import chat_endpoint as chat_handler
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

@router.post("")
@router.post("/")
async def chat_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unified chat endpoint - handles both /chat and /chat/."""
    # Log the raw request body
    body = await request.body()
    logger.info(f"🔍🔍🔍 RAW REQUEST BODY: {body}")
    
    # Log the headers
    logger.info(f"🔍🔍🔍 REQUEST HEADERS: {dict(request.headers)}")
    
    return await chat_handler(request, current_user, db)
