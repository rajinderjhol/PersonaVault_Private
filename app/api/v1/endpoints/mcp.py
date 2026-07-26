from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
from app.core.dependencies import get_current_user
import json
import asyncio
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])

@router.get("/resources")
async def list_resources(request: Request, current_user: int = Depends(get_current_user)):
    """Expose PersonaVault state as MCP Resources for external models."""
    # LEAPFROG: Dynamically include session-specific context
    return {
        "resources": [
            {
                "uri": "personavault://memory/semantic-patterns",
                "name": f"User {current_user} Cognitive Patterns",
                "mimeType": "application/json",
                "description": "Crystallized L3 patterns, preferences, and long-term constraints."
            },
            {
                "uri": "personavault://governance/constitution",
                "name": "Local Guardian Constitution",
                "mimeType": "application/json",
                "description": "Active safety and policy rules"
            },
            {
                "uri": "personavault://blackboard/snapshot",
                "name": "Layer 1 Working Memory",
                "mimeType": "application/json",
                "description": "Real-time insights shared across the cognitive swarm"
            }
        ]
    }

@router.get("/resources/read")
async def read_resource(uri: str, request: Request, current_user: int = Depends(get_current_user)):
    """Standard MCP endpoint to read resource content."""
    if uri == "personavault://memory/semantic-patterns":
        patterns = await request.app.state.semantic_memory.get_recent_patterns(limit=20)
        return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps([{"trigger": p.trigger, "confidence": p.confidence} for p in patterns])}]}
    
    if uri == "personavault://governance/constitution":
        try:
            with open("governance_constitution.json", "r") as f:
                return {"contents": [{"uri": uri, "mimeType": "application/json", "text": f.read()}]}
        except Exception:
            return {"contents": []}
            
    if uri == "personavault://blackboard/snapshot":
        if hasattr(request.app.state, "blackboard"):
            bb = request.app.state.blackboard.get_snapshot()
            return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(bb)}]}
        return {"contents": []}

    raise HTTPException(status_code=404, detail="Resource not found")

@router.get("/tools")
async def list_tools(request: Request):
    """List tools available for external LLMs to call via PersonaVault."""
    return {
        "tools": [
            {
                "name": "vault_search",
                "description": "Search the user's multi-layered memory vault (Vector + SQL)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search terms"},
                        "limit": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "vault_add",
                "description": "Record a new memory into the vault",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "The text to remember"},
                        "tags": {"type": "string", "description": "Comma-separated tags"},
                        "modality": {"type": "string", "default": "text"}
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "get_empathy_context",
                "description": "Get the user's current environmental mood and situational tone",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "blackboard_post",
                "description": "Inject an insight into the cognitive mesh",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "insight": {"type": "string", "description": "Observation to share"}
                    },
                    "required": ["insight"]
                }
            }
        ]
    }

@router.post("/tools/call/{tool_name}")
async def call_tool(tool_name: str, arguments: Dict[str, Any], request: Request, current_user: int = Depends(get_current_user)):
    """Execute a vault tool on behalf of an external model."""
    if tool_name == "vault_search":
        results = await request.app.state.memory_service.search_memories(
            user_id=current_user, 
            query=arguments.get("query", "")
        )
        return {"content": [{"type": "text", "text": json.dumps(results)}]}
    
    if tool_name == "vault_add":
        new_memory = await request.app.state.memory_service.save_memory(
            user_id=current_user,
            memory_type=arguments.get("modality", "text"),
            content=arguments.get("content", ""),
            tags=arguments.get("tags", "")
        )
        return {"content": [{"type": "text", "text": f"Stored in Vault (ID: {new_memory.id})"}]}

    if tool_name == "blackboard_post":
        await request.app.state.blackboard.post_insight(
            agent_name="External-MCP",
            insight=arguments.get("insight", ""),
            importance=0.7
        )
        return {"content": [{"type": "text", "text": "Insight accepted by cognitive mesh."}]}

    if tool_name == "get_empathy_context":
        agent = request.app.state.empathy_agent
        return {"content": [{"type": "text", "text": f"Current Mood: {agent.last_mood}, Tone: {agent.last_tone}"}]}

    return {"error": "Tool not found", "isError": True}

# ============ MCP SSE TRANSPORT (PHASE 3 LEAPFROG) ============

# Registry for active SSE client queues
sse_sessions: Dict[str, asyncio.Queue] = {}

@router.get("/sse")
async def mcp_sse_transport(request: Request):
    """
    Initial SSE connection point for MCP clients (e.g., Claude Desktop).
    Sends the 'endpoint' event to tell the client where to send POST messages.
    """
    session_id = str(uuid.uuid4())
    queue = asyncio.Queue()
    sse_sessions[session_id] = queue
    
    async def event_generator():
        try:
            # 1. Send the endpoint URI to the client
            # The client will use this URL for subsequent JSON-RPC requests
            endpoint_url = f"/api/v1/mcp/messages?session_id={session_id}"
            yield f"event: endpoint\ndata: {endpoint_url}\n\n"
            
            # 2. Keep connection open and relay messages from the queue
            while True:
                if await request.is_disconnected():
                    break
                
                message = await queue.get()
                yield f"event: message\ndata: {json.dumps(message)}\n\n"
                queue.task_done()
                
        finally:
            # Cleanup session on disconnect
            if session_id in sse_sessions:
                del sse_sessions[session_id]
                logger.info(f"MCP SSE Session {session_id} terminated.")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/messages")
async def mcp_receive_message(
    session_id: str, 
    request: Request, 
    background_tasks: BackgroundTasks
):
    """
    Receives JSON-RPC messages from MCP clients and dispatches them to the swarm.
    Responses are sent back through the corresponding SSE stream.
    """
    if session_id not in sse_sessions:
        raise HTTPException(status_code=404, detail="Session expired or not found")

    payload = await request.json()
    method = payload.get("method")
    params = payload.get("params", {})
    msg_id = payload.get("id")

    try:
        result = None
        # JSON-RPC Method Dispatcher for MCP Compliance
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "serverInfo": {"name": "PersonaVault-Sovereign", "version": "1.0.0"}
            }
        elif method == "notifications/initialized":
            logger.info(f"MCP Session {session_id} initialized by client.")
            return {"status": "ok"}
        elif method == "tools/list":
            result = await list_tools(request)
        elif method == "tools/call":
            result = await call_tool(params.get("name"), params.get("arguments", {}), request, current_user=1)
        elif method == "resources/list":
            result = await list_resources(request, current_user=1)
        elif method == "resources/read":
            result = await read_resource(params.get("uri"), request, current_user=1)
        else:
            # Standard JSON-RPC Method Not Found
            if msg_id is not None:
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Method '{method}' not implemented"}
                }
                await sse_sessions[session_id].put(response)
            return {"status": "method_not_supported"}

        # Send result back via the SSE stream for the specific session
        if msg_id is not None and result is not None:
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
            await sse_sessions[session_id].put(response)
        
        return {"status": "accepted"}

    except Exception as e:
        logger.error(f"MCP Dispatcher Error: {e}")
        if msg_id is not None:
            error_resp = {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32603, "message": str(e)}}
            await sse_sessions[session_id].put(error_resp)
        return {"status": "error", "message": str(e)}