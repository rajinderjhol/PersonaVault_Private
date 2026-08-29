import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.swarm.core.generator import GeneratorAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat-stream"])


class ChatRequest(BaseModel):
    query: str
    provider: str = "auto"
    user_id: int = 1
    session_id: Optional[str] = None
    force_domain: Optional[str] = None


@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """Stream chat response with premium UX - real-time feedback."""
    
    generator = GeneratorAgent()
    
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # 1. Send initial "thinking" status
            yield f"data: {json.dumps({'type': 'status', 'message': '🔍 Analyzing your query...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # 2. Get domain detection
            domain_result = await generator.domain_router.route(query=request.query)
            yield f"data: {json.dumps({'type': 'status', 'message': f'🎯 Domain detected: {domain_result.domain}'})}\n\n"
            await asyncio.sleep(0.1)
            
            # 3. Show crystallized patterns if found
            if domain_result.patterns:
                yield f"data: {json.dumps({'type': 'status', 'message': f'💎 Found {len(domain_result.patterns)} crystallized patterns'})}\n\n"
                await asyncio.sleep(0.1)
            
            # 4. Send "generating" status
            yield f"data: {json.dumps({'type': 'status', 'message': '🧠 Generating response...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # 5. Stream the actual response
            first_chunk = True
            async for chunk in generator.generate_stream_with_trace(
                query=request.query,
                provider=request.provider,
                user_id=request.user_id
            ):
                if chunk.get("type") == "content":
                    content = chunk.get("content", "")
                    # Send content chunk
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                    if first_chunk:
                        # Once we start sending content, clear the status
                        yield f"data: {json.dumps({'type': 'status', 'message': '💬 Responding...'})}\n\n"
                        first_chunk = False
                
                elif chunk.get("type") == "trace":
                    # Send the full trace with metadata at the end
                    yield f"data: {json.dumps({
                        'type': 'trace', 
                        'trace': chunk.get('trace'), 
                        'memory_status': chunk.get('memory_status'),
                        'suggestions': chunk.get('suggestions'),
                        'domain': chunk.get('domain'), 
                        'domain_confidence': chunk.get('domain_confidence')
                    })}\n\n"
            
            # 6. Send completion status
            yield f"data: {json.dumps({'type': 'status', 'message': '✅ Complete'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
