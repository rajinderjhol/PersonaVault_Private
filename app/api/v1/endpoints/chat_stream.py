"""
Chat Streaming Endpoint - Orchestrator Streaming
"""
import json
import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import logging

from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest
from app.swarm.orchestrator import get_orchestrator
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat-stream"])

@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """Stream chat response with orchestrator swarm intelligence"""
    
    async def generate() -> AsyncGenerator[str, None]:
        try:
            logger.info(f"Streaming request for user {current_user.id}: {request.query[:50]}...")
            
            # Send start event
            yield f"event: start\ndata: {json.dumps({'message': 'Starting generation...', 'provider': request.provider})}\n\n"
            
            # Process with orchestrator streaming
            async for db in get_db():
                orchestrator = get_orchestrator(db_session=db, blackboard=None)
                
                # Stream from orchestrator
                async for event in orchestrator.stream_process(
                    query=request.query,
                    user_id=current_user.id,
                    session_id=request.session_id,
                    provider=request.provider or "groq"
                ):
                    event_type = event.get("type")
                    event_data = event.get("data")
                    
                    if event_type == "thought":
                        # Send thought process
                        yield f"data: {json.dumps({'thought': event_data})}\n\n"
                    
                    elif event_type == "content":
                        # Send content chunk
                        yield f"data: {json.dumps({'content': event_data})}\n\n"
                    
                    elif event_type == "session_id":
                        # Send session ID
                        yield f"data: {json.dumps({'session_id': event_data})}\n\n"
                    
                    elif event_type == "error":
                        # Send error
                        yield f"event: error\ndata: {json.dumps({'error': event_data})}\n\n"
                    
                    elif event_type == "done":
                        # Send done event
                        yield f"event: done\ndata: {json.dumps({'message': 'Generation complete'})}\n\n"
                    
                    await asyncio.sleep(0.001)
                
                break
                
        except Exception as e:
            logger.error(f"Stream error: {e}")
            import traceback
            traceback.print_exc()
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
