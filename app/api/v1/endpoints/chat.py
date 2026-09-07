"""
Chat API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.dependencies import get_current_user
from app.models import User
from app.services.intelligence_gateway import gateway
from app.services.trace_service import TraceService, TraceStep
from app.swarm.routing.domain_detector import DomainDetector
from app.db.session import get_db
from app.utils.time_parser import TimeParser
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

@router.post("/")
async def chat_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Unified chat endpoint - uses the Intelligence Gateway.
    """
    result = None
    try:
        data = await request.json()
        query = data.get("query", "")
        patient_id = data.get("patient_id")
        provider = data.get("provider", "ollama")
        
        # Domain detection
        domain_detector = DomainDetector()
        result_domain = await domain_detector.detect(query)
        pack_name = result_domain.domain or "general"
        
        # Temporal Intelligence integration
        temporal_context = TimeParser.parse(query)
        
        # If provider is not available, try fallback
        available_providers = ["ollama", "groq", "gemini"]
        if provider not in available_providers:
            logger.warning(f"Unknown provider {provider}, falling back to ollama")
            provider = "ollama"
            
        session_id = data.get("session_id", 0)
        
        logger.info(f"🔍 DEBUG: Chat endpoint received provider: '{provider}' for query: '{query}'")
        
        if not query:
            return {"error": "Query is required"}
        
        # Get response
        logger.info(f"🔍 DEBUG: Calling gateway.chat with provider: '{provider}'")
        result = await gateway.chat(
            user_id=current_user.id,
            query=query,
            state=request.app.state,
            patient_id=patient_id,
            provider=provider
        )
        
        # Capture trace
        trace_service = TraceService(db)
        await trace_service.capture_step(
            session_id=session_id,
            step=TraceStep.PERCEPTION,
            data={"query": query, "domain": pack_name},
            agent_id="ChatRouter",
            confidence_score=0.95,
            query=query,
            pack_name=pack_name,
            user_id=current_user.id
        )
        
        # Self-improving intelligence
        if hasattr(request.app.state, "self_improving"):
            # Using finalResponse instead of response
            response_text = result.get("finalResponse", "")
            
            # Extract patterns in the background
            asyncio.create_task(
                request.app.state.self_improving.analyze_interaction(
                    current_user.id,
                    query,
                    response_text,
                    0.8, # Placeholder confidence
                    {"provider": provider, "session_id": session_id}
                )
            )
            
            # Apply learned patterns
            enhanced_response = await request.app.state.self_improving.apply_patterns_to_response(
                query, response_text
            )
            if enhanced_response != response_text:
                result["finalResponse"] = enhanced_response
                result["pattern_applied"] = True
        
        return result
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return {"error": str(e), "response": f"[Error: {str(e)}]"}
