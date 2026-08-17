"""
Ollama Connection Manager - Stateful, reusable connections
Prevents timeout issues by maintaining persistent connections
"""
import asyncio
import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OllamaManager:
    """Stateful Ollama connection manager with connection pooling."""
    
    _instance = None
    _client: Optional[httpx.AsyncClient] = None
    _last_health_check: Optional[datetime] = None
    _is_healthy: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._client = None
        self._last_health_check = None
        self._is_healthy = False
        self._warmup_done = False
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create a persistent HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
                http2=True
            )
            # Warm up the connection
            await self._warmup()
        return self._client
    
    async def _warmup(self):
        """Warm up the connection to Ollama."""
        if self._warmup_done:
            return
        
        try:
            # Simple health check
            response = await self._client.get("http://localhost:11434/api/tags", timeout=5.0)
            if response.status_code == 200:
                self._is_healthy = True
                self._last_health_check = datetime.now()
                logger.info("✅ Ollama connection established")
                
                # Pre-warm the model (optional, but helps)
                try:
                    await self._client.post(
                        "http://localhost:11434/api/generate",
                        json={"model": "tinydolphin", "prompt": "Hello", "stream": False},
                        timeout=10.0
                    )
                    logger.info("✅ Ollama model warmed up")
                except:
                    pass  # Model warmup is optional
                
                self._warmup_done = True
        except Exception as e:
            logger.warning(f"Ollama warmup failed: {e}")
            self._is_healthy = False
    
    async def generate(self, prompt: str, model: str = "tinydolphin", **kwargs) -> Dict[str, Any]:
        """Generate a response using the persistent connection."""
        client = await self.get_client()
        
        try:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    **kwargs
                },
                timeout=60.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return {"error": f"Ollama error {response.status_code}"}
        except httpx.TimeoutException:
            logger.error("Ollama timeout")
            return {"error": "Timeout"}
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return {"error": str(e)}
    
    async def chat(self, messages: list, model: str = "tinydolphin", **kwargs) -> Dict[str, Any]:
        """Chat with Ollama using the persistent connection."""
        client = await self.get_client()
        
        try:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    **kwargs
                },
                timeout=60.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Ollama error {response.status_code}"}
        except httpx.TimeoutException:
            return {"error": "Timeout"}
        except Exception as e:
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Check if Ollama is healthy."""
        try:
            client = await self.get_client()
            response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
            self._is_healthy = response.status_code == 200
            self._last_health_check = datetime.now()
            return self._is_healthy
        except:
            self._is_healthy = False
            return False
    
    async def close(self):
        """Close the connection."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
        self._client = None
        self._warmup_done = False

# Global instance
ollama_manager = OllamaManager()
