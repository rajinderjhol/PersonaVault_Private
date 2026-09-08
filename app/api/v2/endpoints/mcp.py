from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.mcp.manager import MCPServerManager
from app.core.dependencies import get_current_user

router = APIRouter(tags=["mcp"])
manager = MCPServerManager()

class ServerInstallRequest(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    command: str = "python"
    args: Optional[List[str]] = []
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = {}
    tools: Optional[List[str]] = []
    enabled: bool = True

@router.get("/servers")
async def list_servers(current_user = Depends(get_current_user)):
    """List all MCP servers."""
    return {"servers": manager.list_servers()}

@router.get("/servers/{server_id}/status")
async def get_server_status(server_id: str, current_user = Depends(get_current_user)):
    """Get MCP server status."""
    return manager.get_status(server_id)

@router.post("/servers/{server_id}/connect")
async def connect_server(server_id: str, current_user = Depends(get_current_user)):
    """Connect to an MCP server."""
    return await manager.connect_server(server_id)

@router.post("/servers/{server_id}/disconnect")
async def disconnect_server(server_id: str, current_user = Depends(get_current_user)):
    """Disconnect from an MCP server."""
    return await manager.disconnect_server(server_id)

@router.post("/servers/{server_id}/tools/{tool_name}")
async def call_tool(
    server_id: str,
    tool_name: str,
    params: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Call a tool on an MCP server."""
    return await manager.call_tool(server_id, tool_name, params)

@router.post("/servers/install")
async def install_server(
    request: ServerInstallRequest,
    current_user = Depends(get_current_user)
):
    """Install a new MCP server."""
    return await manager.install_server(request.dict())

@router.delete("/servers/{server_id}")
async def uninstall_server(server_id: str, current_user = Depends(get_current_user)):
    """Uninstall an MCP server."""
    return await manager.uninstall_server(server_id)
