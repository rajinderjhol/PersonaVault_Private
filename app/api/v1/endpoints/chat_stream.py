"""
Chat Stream Endpoint - Domain-aware streaming chat
"""

import json
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.swarm.core.generator import GeneratorAgent

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    provider: str = "auto"
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    force_domain: Optional[str] = None
    track_thoughts: bool = True


class ChatResponse(BaseModel):
    content: str
    domain: Optional[str] = None
    domain_confidence: Optional[float] = None


@router.post("/stream")
async def stream_chat(request: ChatRequest) -> StreamingResponse:
    """
    Stream chat response with domain awareness.
    """
    logger.info(f"Chat request: {request.query[:50]}... (provider: {request.provider})")
    
    # Initialize generator
    generator = GeneratorAgent()
    
    # Get context (memories) if user_id provided
    context = None
    if request.user_id:
        try:
            from app.services.memory.ice_repository import IceMemoryRepository
            memory_repo = IceMemoryRepository()
            memories = await memory_repo.get_relevant_memories(
                query=request.query,
                user_id=request.user_id,
                limit=5
            )
            context = memories
        except Exception as e:
            logger.warning(f"Failed to load memories: {e}")
    
    async def event_generator():
        """Generate SSE events."""
        try:
            domain_result = None
            
            # Stream response
            async for chunk in generator.generate_stream(
                query=request.query,
                provider=request.provider,
                context=context,
                force_domain=request.force_domain
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            # Send completion event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/chat")
async def chat(request: ChatRequest) -> Dict[str, Any]:
    """
    Non-streaming chat with domain awareness.
    """
    generator = GeneratorAgent()
    
    context = None
    if request.user_id:
        try:
            from app.services.memory.ice_repository import IceMemoryRepository
            memory_repo = IceMemoryRepository()
            memories = await memory_repo.get_relevant_memories(
                query=request.query,
                user_id=request.user_id,
                limit=5
            )
            context = memories
        except Exception as e:
            logger.warning(f"Failed to load memories: {e}")
    
    result = await generator.generate(
        query=request.query,
        context=context
    )
    
    return {
        "answer": result.get("answer"),
        "source": result.get("source"),
        "confidence": result.get("confidence"),
        "domain": result.get("domain"),
        "domain_confidence": result.get("domain_confidence"),
        "trace": result.get("trace")
    }


@router.get("/domains")
async def list_domains() -> Dict[str, Any]:
    """
    List all available domains.
    """
    generator = GeneratorAgent()
    stats = generator.domain_router.get_domain_stats()
    state = generator.domain_router.get_conversation_state()
    
    return {
        "domains": stats,
        "conversation": state
    }


@router.post("/domains/reset")
async def reset_domain_conversation() -> Dict[str, str]:
    """
    Reset the domain conversation state.
    """
    generator = GeneratorAgent()
    generator.domain_router.reset_conversation()
    return {"status": "reset"}
