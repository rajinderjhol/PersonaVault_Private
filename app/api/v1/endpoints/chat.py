"""
Chat API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.dependencies import get_current_user
from app.models import User
from app.services.intelligence_gateway import gateway
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

@router.post("/")
async def chat_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user)
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
        
        # If provider is not available, try fallback
        available_providers = ["ollama", "groq", "gemini"]
        if provider not in available_providers:
            logger.warning(f"Unknown provider {provider}, falling back to ollama")
            provider = "ollama"
            
        session_id = data.get("session_id")
        
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
        logger.info(f"🔍 DEBUG: gateway.chat returned response from provider: '{result.get('provider')}'")
        
        # Self-improving intelligence
        if hasattr(request.app.state, "self_improving"):
            confidence = result.get("confidence", 0.7)
            response_text = result.get("response", "")
            
            # Extract patterns in the background
            asyncio.create_task(
                request.app.state.self_improving.analyze_interaction(
                    current_user.id,
                    query,
                    response_text,
                    confidence,
                    {"provider": provider, "session_id": session_id}
                )
            )
            
            # Apply learned patterns
            enhanced_response = await request.app.state.self_improving.apply_patterns_to_response(
                query, response_text
            )
            if enhanced_response != response_text:
                result["response"] = enhanced_response
                result["pattern_applied"] = True
        
        return result
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return {"error": str(e), "response": f"[Error: {str(e)}]"}
