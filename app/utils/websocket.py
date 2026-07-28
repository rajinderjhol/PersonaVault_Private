from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages active WebSocket connections for real-time telemetry and messaging."""
    def __init__(self):
        # Dictionary mapping client_id (user_id) to a set of active connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, client_id: str, websocket: WebSocket):
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        self.active_connections[client_id].add(websocket)
    
    def disconnect(self, client_id: str, websocket: WebSocket):
        if client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)
            # Clean up key if no more connections for this user
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
    
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            for connection in list(self.active_connections[client_id]):
                try:
                    await connection.send_text(message)
                except Exception:
                    self.disconnect(client_id, connection)

    async def broadcast(self, message: str):
        """Send a message to all connected clients."""
        for client_id in list(self.active_connections.keys()):
            for connection in list(self.active_connections[client_id]):
                try:
                    await connection.send_text(message)
                except Exception:
                    self.disconnect(client_id, connection)

manager = ConnectionManager()