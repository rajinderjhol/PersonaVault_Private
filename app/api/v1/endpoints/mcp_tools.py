"""
MCP Tools API endpoints.
"""
from fastapi import APIRouter, Depends, Request
from app.core.dependencies import get_current_user
from app.models import User
from app.services.intelligence_gateway import MCPRegistry
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mcp", tags=["mcp"])

@router.get("/tools")
async def list_mcp_tools():
    """List all available MCP tools."""
    return {"tools": MCPRegistry.list_tools()}

@router.post("/call/{tool_name}")
async def call_mcp_tool(
    tool_name: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Call any MCP tool by name."""
    try:
        data = await request.json()
        result = await MCPRegistry.call(tool_name, **data)
        return result
    except Exception as e:
        logger.error(f"MCP call error: {e}")
        return {"success": False, "error": str(e)}
