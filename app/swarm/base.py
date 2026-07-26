import httpx
import logging
from typing import Optional

class BaseAgent:
    """Foundation for all PersonaVault Swarm Agents."""
    def __init__(self, name: str, client: Optional[httpx.AsyncClient] = None):
        self.name = name
        self._client = client
        self.logger = logging.getLogger(f"persona.swarm.{name}")

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy access to a shared AsyncClient."""
        if not self._client:
            self.logger.debug(f"Agent {self.name}: Initializing local AsyncClient.")
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client