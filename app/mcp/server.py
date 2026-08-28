"""
MCP Server - Execute actions on connected integrations
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.mcp.registry import IntegrationRegistry

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Server for executing actions on integrations."""
    
    def __init__(self):
        self.registry = IntegrationRegistry()
    
    async def execute(
        self,
        integration_id: str,
        action: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an action on an integration."""
        connection = await self.registry.get_connection(integration_id)
        if not connection:
            raise ValueError(f"Integration {integration_id} is not connected")
        
        integrations = await self.registry.list_all()
        integration = next((i for i in integrations if i["id"] == integration_id), None)
        if not integration:
            raise ValueError(f"Integration {integration_id} not found")
        
        # Verify action is supported
        available_tools = integration.get("tools", [])
        if action not in available_tools:
            raise ValueError(f"Action '{action}' not supported for integration {integration_id}")
        
        try:
            handler = self._get_action_handler(integration_id, action)
            result = await handler(connection, params)
            return {
                "success": True,
                "action": action,
                "result": result,
                "executed_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to execute action {action} on {integration_id}: {e}")
            return {
                "success": False,
                "action": action,
                "error": str(e)
            }
    
    async def list_tools(self, integration_id: str) -> list:
        integrations = await self.registry.list_all()
        integration = next((i for i in integrations if i["id"] == integration_id), None)
        if not integration:
            return []
        return integration.get("tools", [])
    
    def _get_action_handler(self, integration_id: str, action: str):
        handlers = {
            "calendar": {
                "list_events": self._handle_calendar_list_events,
                "create_event": self._handle_calendar_create_event
            },
            "discord": {
                "send_message": self._handle_discord_send_message,
                "get_status": self._handle_discord_get_status
            },
            "twilio": {
                "send_sms": self._handle_twilio_send_sms,
                "get_status": self._handle_twilio_get_status
            },
            "email": {
                "send_email": self._handle_email_send_email,
                "list_emails": self._handle_email_list_emails
            },
            "telegram": {
                "send_message": self._handle_telegram_send_message,
                "get_status": self._handle_telegram_get_status
            }
        }
        return handlers.get(integration_id, {}).get(action, self._handle_default)
    
    async def _handle_default(self, connection: Dict, params: Dict) -> Dict:
        return {"message": "Action not implemented", "params": params}
    
    # Mock Handlers
    async def _handle_calendar_list_events(self, connection: Dict, params: Dict) -> Dict:
        return {"events": [{"summary": "Team Meeting", "start": "2026-08-29T10:00:00Z"}], "count": 1}
    
    async def _handle_calendar_create_event(self, connection: Dict, params: Dict) -> Dict:
        return {"event_id": "evt_123456", "summary": params.get("summary", "New Event")}
    
    async def _handle_discord_send_message(self, connection: Dict, params: Dict) -> Dict:
        return {"message_id": "msg_123456", "sent": True}
    
    async def _handle_discord_get_status(self, connection: Dict, params: Dict) -> Dict:
        return {"online": True, "server_count": 5}
    
    async def _handle_twilio_send_sms(self, connection: Dict, params: Dict) -> Dict:
        return {"message_sid": "SM123456", "status": "sent"}
    
    async def _handle_twilio_get_status(self, connection: Dict, params: Dict) -> Dict:
        return {"balance": "12.50", "sent_count": 156}
    
    async def _handle_email_send_email(self, connection: Dict, params: Dict) -> Dict:
        return {"message_id": "msg_123456", "status": "sent"}
    
    async def _handle_email_list_emails(self, connection: Dict, params: Dict) -> Dict:
        return {"emails": [{"id": "1", "subject": "Welcome"}], "count": 1}
    
    async def _handle_telegram_send_message(self, connection: Dict, params: Dict) -> Dict:
        return {"message_id": 123456, "sent": True}
    
    async def _handle_telegram_get_status(self, connection: Dict, params: Dict) -> Dict:
        return {"connected": True, "chat_count": 12}
