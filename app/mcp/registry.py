import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class IntegrationRegistry:
    """Registry for MCP integrations."""
    
    def __init__(self):
        self.integrations_dir = Path("app/mcp/integrations")
        self.data_dir = Path("data")
        self.connected_path = self.data_dir / "connected_integrations.json"
        self._integrations = {}
        self._load_integrations()
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_integrations(self):
        if not self.integrations_dir.exists():
            logger.warning(f"Integrations directory not found: {self.integrations_dir}")
            return
        
        for config_file in self.integrations_dir.glob("*/config.json"):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    integration_id = config.get("id", config_file.parent.name)
                    self._integrations[integration_id] = config
                    logger.info(f"Loaded integration: {integration_id}")
            except Exception as e:
                logger.error(f"Failed to load integration {config_file}: {e}")
    
    async def list_all(self) -> List[Dict[str, Any]]:
        return [{
            "id": idx,
            "name": config.get("name", idx),
            "description": config.get("description", ""),
            "icon": config.get("icon", "🔌"),
            "category": config.get("category", "general"),
            "auth_type": config.get("auth_type", "api_key"),
            "status": "available",
            "tools": config.get("tools", [])
        } for idx, config in self._integrations.items()]
    
    async def list_connected(self) -> List[Dict[str, Any]]:
        connected = await self._load_connected()
        return [{
            "id": conn["id"],
            "name": self._integrations.get(conn["id"], {}).get("name", conn["id"]),
            "connected_at": conn["connected_at"],
            "status": "connected"
        } for conn in connected if conn["id"] in self._integrations]
    
    async def connect(self, integration_id: str, auth: Dict) -> Dict:
        if integration_id not in self._integrations:
            raise ValueError(f"Integration {integration_id} not found")
        
        connection = {
            "id": integration_id,
            "auth_type": auth.get("type"),
            "connected_at": datetime.now().isoformat(),
            "credentials": auth.get("credentials", {})
        }
        
        connected = await self._load_connected()
        connected = [c for c in connected if c["id"] != integration_id]
        connected.append(connection)
        await self._save_connected(connected)
        
        return {"status": "connected", "details": connection}
    
    async def disconnect(self, integration_id: str):
        connected = await self._load_connected()
        connected = [c for c in connected if c["id"] != integration_id]
        await self._save_connected(connected)
    
    async def get_status(self, integration_id: str) -> Dict:
        connected = await self._load_connected()
        connection = next((c for c in connected if c["id"] == integration_id), None)
        return {
            "integration_id": integration_id,
            "is_connected": connection is not None,
            "available": integration_id in self._integrations,
            "details": self._integrations.get(integration_id, {}),
            "connected_at": connection.get("connected_at") if connection else None
        }
    
    async def get_connection(self, integration_id: str) -> Optional[Dict]:
        connected = await self._load_connected()
        return next((c for c in connected if c["id"] == integration_id), None)

    async def _load_connected(self) -> List[Dict]:
        if self.connected_path.exists():
            try:
                with open(self.connected_path, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    async def _save_connected(self, connected: List[Dict]):
        self.connected_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.connected_path, 'w') as f:
            json.dump(connected, f, indent=2)
