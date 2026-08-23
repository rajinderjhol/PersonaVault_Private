"""
PersonaVault Swarm Agent.
"""
from typing import Dict, Any, Optional

class SwarmAgent:
    """Interface to the PersonaVault swarm intelligence."""
    
    def __init__(self, client):
        self._client = client
    
    def chat(self, query: str, provider: str = "ollama", context: str = "") -> Dict[str, Any]:
        """Send a message to the swarm."""
        response = self._client._client.post(
            "/api/v1/chat/",
            headers=self._client._headers,
            json={"query": query, "provider": provider}
        )
        response.raise_for_status()
        return response.json()
    
    def decide(self, problem: str, domain: str = "general") -> Dict[str, Any]:
        """Generate a decision using the swarm."""
        response = self._client._client.post(
            "/api/v1/generative/decide",
            headers=self._client._headers,
            json={"problem": problem, "context": {"domain": domain}}
        )
        response.raise_for_status()
        return response.json()
