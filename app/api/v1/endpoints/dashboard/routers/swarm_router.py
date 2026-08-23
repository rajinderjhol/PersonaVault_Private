"""
Swarm Router - Multi-agent orchestration endpoints
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from app.core.dependencies import require_admin
from app.utils.websocket import manager
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/swarm", tags=["admin"])

@router.post("/trigger")
async def trigger_swarm_interaction(
    request: Request,
    body: dict,
    user_id: int = Depends(require_admin)
):
    """Directly inject a query into the Swarm and process it."""
    query = body.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query content required")
    
    blackboard = getattr(request.app.state, "blackboard", None)
    orchestrator = getattr(request.app.state, "orchestrator", None)
    
    if not blackboard:
        return {"status": "error", "message": "Blackboard not available"}
    
    await blackboard.post_insight(
        agent_name="Admin-Terminal",
        insight={"query": query, "status": "processing", "origin": "dashboard"},
        importance=1.0
    )
    
    await manager.broadcast(json.dumps({
        "type": "thought_stream",
        "agent": "Orchestrator",
        "content": f"🚀 Processing query: '{query[:50]}...'"
    }))
    
    if orchestrator:
        try:
            result = await orchestrator.run(
                query=query,
                context={"user_id": user_id, "origin": "dashboard"}
            )
            
            await blackboard.post_insight(
                agent_name="Orchestrator",
                insight={
                    "query": query,
                    "status": "completed",
                    "answer": result.get("answer", "No answer generated"),
                    "evaluation": result.get("evaluation", {}),
                    "confidence": result.get("confidence", 0.0)
                },
                importance=0.9
            )
            
            await manager.broadcast(json.dumps({
                "type": "thought_stream",
                "agent": "Orchestrator",
                "content": f"✅ Query processed successfully!"
            }))
            
            return {
                "status": "swarm_completed",
                "message": f"Query processed: {query[:50]}...",
                "result": result.get("answer", ""),
                "confidence": result.get("confidence", 0.0),
                "evaluation": result.get("evaluation", {})
            }
        except Exception as e:
            logger.error(f"Swarm processing error: {e}")
            await blackboard.post_insight(
                agent_name="Orchestrator",
                insight={
                    "query": query,
                    "status": "error",
                    "error": str(e)
                },
                importance=0.5
            )
            return {
                "status": "swarm_error",
                "message": f"Error processing query: {str(e)}"
            }
    
    return {"status": "swarm_ignited", "message": f"Query '{query}' posted to Blackboard."}

@router.get("/negotiation-trace")
async def get_negotiation_trace(
    request: Request,
    user_id: int = Depends(require_admin)
):
    """Get the real swarm negotiation trace from blackboard history."""
    blackboard = getattr(request.app.state, "blackboard", None)
    if blackboard and hasattr(blackboard, 'history'):
        history = blackboard.history[-10:]
        sequence = []
        for i in range(len(history)):
            step = history[i]
            target = history[i+1].get("agent", "Blackboard") if i < len(history) - 1 else "Blackboard"
            sequence.append({
                "agent": step.get("agent", "Unknown"),
                "to": target,
                "action": step.get("data", {}).get("event", "insight")
            })
        return {"sequence": sequence}
    return {"sequence": []}
