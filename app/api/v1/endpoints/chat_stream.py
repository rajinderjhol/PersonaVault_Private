"""
Streaming Chat Endpoint with Server-Sent Events (SSE)
"""
import json
import logging
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.core.dependencies import get_current_user_id
# Note: Assuming MultiAgentOrchestrator is available in app.swarm.orchestrator
# If this import fails, we might need to adjust based on actual project structure.
from app.swarm.orchestrator import MultiAgentOrchestrator
from app.services.intelligence_gateway import gateway

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat-stream"])

class StreamChatRequest(BaseModel):
    query: str
    provider: Optional[str] = "ollama"
    session_id: Optional[int] = None
    stream: bool = True

@router.post("/stream")
async def stream_chat(
    request: StreamChatRequest,
    req: Request,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream chat response with Server-Sent Events.
    Sends tokens as they're generated with real-time thought process.
    """
    logger.info(f"📡 Streaming chat for user {user_id} with provider {request.provider}")
    
    # Get orchestrator from app state
    orchestrator = req.app.state.orchestrator
    
    # Build provider chain
    providers = ["ollama", "groq", "gemini"]
    if request.provider in providers:
        provider_chain = [request.provider] + [p for p in providers if p != request.provider]
    else:
        provider_chain = providers
    
    async def generate() -> AsyncGenerator[str, None]:
        """Generate SSE stream with thoughts and tokens."""
        try:
            # Step 1: Planning
            yield f"data: {json.dumps({'type': 'thought', 'step': 1, 'label': 'Planning', 'description': 'Analyzing query...', 'status': 'in-progress'})}\n\n"
            
            # Get context
            context = {"user_id": user_id}
            
            # Step 2: Retrieval (parallel with planning)
            yield f"data: {json.dumps({'type': 'thought', 'step': 2, 'label': 'Retrieval', 'description': 'Searching memories...', 'status': 'in-progress'})}\n\n"
            
            # Run the orchestrator pipeline
            result = await orchestrator.run(request.query, context)
            
            # Step 3: Generation (streaming)
            yield f"data: {json.dumps({'type': 'thought', 'step': 3, 'label': 'Generation', 'description': 'Synthesizing response...', 'status': 'in-progress'})}\n\n"
            
            # Get the response
            full_response = result.get("answer", "No response generated")
            confidence = result.get("confidence", 0.0)
            evaluation = result.get("evaluation", {})
            
            # Stream tokens
            words = full_response.split()
            for i, word in enumerate(words):
                # Send token
                yield f"data: {json.dumps({'type': 'token', 'token': word + ' '})}\n\n"
                
                # Send progress every 5 words
                if i % 5 == 0:
                    progress = min(100, int((i + 1) / len(words) * 100))
                    yield f"data: {json.dumps({'type': 'progress', 'percent': progress})}\n\n"
            
            # Step 4: Evaluation
            evaluation_desc = f'Quality: {evaluation.get("passed", True)}'
            yield f'data: {json.dumps({"type": "thought", "step": 4, "label": "Evaluation", "description": evaluation_desc, "status": "complete"})}\n\n'
            
            # Step 5: Done
            yield f'data: {json.dumps({"type": "done", "confidence": confidence, "provider": request.provider, "thought_process": result.get("thought_process", [])})}\n\n'
            
            logger.info(f"✅ Streaming complete for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
