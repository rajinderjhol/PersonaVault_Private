"""
Integrations Endpoints - Connect PersonaVault to external services
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.mcp.registry import IntegrationRegistry
from app.mcp.server import MCPServer

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


class IntegrationAuth(BaseModel):
    type: str
    credentials: Dict[str, str]


class IntegrationAction(BaseModel):
    action: str
    params: Dict[str, Any]


@router.get("/")
async def list_integrations() -> Dict[str, Any]:
    """List all available integrations."""
    registry = IntegrationRegistry()
    return {
        "integrations": await registry.list_all(),
        "connected": await registry.list_connected()
    }


@router.get("/{integration_id}/status")
async def get_integration_status(integration_id: str) -> Dict[str, Any]:
    """Get the status of an integration."""
    registry = IntegrationRegistry()
    return await registry.get_status(integration_id)


@router.post("/{integration_id}/connect")
async def connect_integration(
    integration_id: str,
    auth: IntegrationAuth
) -> Dict[str, Any]:
    """Connect an integration with authentication."""
    registry = IntegrationRegistry()
    try:
        result = await registry.connect(integration_id, auth.dict())
        return {
            "integration_id": integration_id,
            "status": "connected",
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{integration_id}/disconnect")
async def disconnect_integration(
    integration_id: str
) -> Dict[str, Any]:
    """Disconnect an integration."""
    registry = IntegrationRegistry()
    await registry.disconnect(integration_id)
    return {
        "integration_id": integration_id,
        "status": "disconnected"
    }


@router.post("/{integration_id}/actions")
async def execute_action(
    integration_id: str,
    action: IntegrationAction
) -> Dict[str, Any]:
    """Execute an action on an integration."""
    mcp = MCPServer()
    try:
        result = await mcp.execute(
            integration_id=integration_id,
            action=action.action,
            params=action.params
        )
        return {
            "integration_id": integration_id,
            "action": action.action,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{integration_id}/tools")
async def list_tools(
    integration_id: str
) -> List[Dict[str, Any]]:
    """List available tools for an integration."""
    mcp = MCPServer()
    return await mcp.list_tools(integration_id)
