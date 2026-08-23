"""
PersonaVault Python SDK Client.
"""
import httpx
from typing import Dict, Any, List, Optional
from .models import Decision, Pattern, Memory, AuditLog
from .swarm import SwarmAgent

class DecisionManager:
    """Handles decision-related API calls."""
    def __init__(self, client):
        self._client = client
        
    def create(self, **kwargs) -> Decision:
        response = self._client._client.post(
            "/api/v1/behaviour/event",
            headers=self._client._headers,
            json=kwargs
        )
        response.raise_for_status()
        return Decision(**response.json())
        
    def list(self) -> List[Decision]:
        # Implementation for listing decisions
        pass

class PersonaVault:
    """Main client for PersonaVault API."""
    
    def __init__(self, host: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.host = host
        self.api_key = api_key
        self._client = httpx.Client(base_url=host, timeout=30.0)
        self._headers = {}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"
        
        self._decisions = DecisionManager(self)
        self._swarm = SwarmAgent(self)
    
    def login(self, username: str, password: str):
        """Login and get session cookie."""
        response = self._client.post("/api/v1/auth/login", json={
            "username": username,
            "password": password
        })
        response.raise_for_status()
        # Set cookie for subsequent requests
        session_id = response.cookies.get('session_id')
        if session_id:
            self._headers["Cookie"] = f"session_id={session_id}"
        return self
    
    @property
    def decisions(self) -> DecisionManager:
        """Decision management."""
        return self._decisions
    
    @property
    def swarm(self) -> SwarmAgent:
        """Swarm intelligence."""
        return self._swarm
    
    def __repr__(self):
        return f"<PersonaVault({self.host})>"
