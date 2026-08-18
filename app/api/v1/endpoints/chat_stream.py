
"""
Streaming Chat Endpoint
Server-Sent Events for real-time token streaming
"""
import asyncio
import json
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

from app.core.dependencies import get_current_user
from app.models import User
from app.services.intelligence_gateway import gateway

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat-stream"])

@router.post("/stream")
async def stream_chat(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Stream chat response using Server-Sent Events.
    Tokens are sent as they are generated.
    """
    try:
        data = await request.json()
        query = data.get("query", "")
        provider = data.get("provider", "ollama")
        
        if not query:
            return {"error": "Query is required"}
        
        logger.info(f"📡 Streaming chat for user {current_user.id} with provider {provider}")
        
        async def generate() -> AsyncGenerator[dict, None]:
            """Generate SSE events for streaming."""
            try:
                # Send start event
                yield {
                    "event": "start",
                    "data": json.dumps({
                        "message": "Starting generation...",
                        "provider": provider
                    })
                }
                
                # Use orchestrator for retrieval + generation
                orchestrator = request.app.state.orchestrator
                
                # Run the orchestrator with streaming
                result = await orchestrator.run(
                    query, 
                    {"user_id": current_user.id, "provider": provider}
                )
                
                response_text = result.get("answer", "")
                confidence = result.get("confidence", 0.0)
                evaluation = result.get("evaluation", {})
                thought_process = result.get("thought_process", [])
                
                # Send thought process as events
                for step in thought_process:
                    yield {
                        "event": "thought",
                        "data": json.dumps({
                            "step": step.get("step", 0),
                            "label": step.get("label", ""),
                            "description": step.get("description", ""),
                            "status": step.get("status", "complete"),
                            "duration": step.get("duration", 0)
                        })
                    }
                    await asyncio.sleep(0.05)
                
                # Stream tokens word by word
                if response_text:
                    words = response_text.split()
                    total_words = len(words)
                    
                    for i, word in enumerate(words):
                        progress = int((i + 1) / total_words * 100) if total_words > 0 else 0
                        
                        # Send token event
                        yield {
                            "event": "token",
                            "data": json.dumps({
                                "token": word + " ",
                                "progress": progress
                            })
                        }
                        # Small delay for visual effect
                        await asyncio.sleep(0.015)
                
                # Send completion event
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "confidence": confidence,
                        "evaluation": evaluation,
                        "provider": provider,
                        "total_tokens": len(response_text.split()),
                        "total_time_ms": result.get("total_time_ms", 0)
                    })
                }
                
            except Exception as e:
                logger.error(f"Streaming error: {e}", exc_info=True)
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)})
                }
        
        return EventSourceResponse(generate())
        
    except Exception as e:
        logger.error(f"Stream endpoint error: {e}", exc_info=True)
        return {"error": str(e)}
