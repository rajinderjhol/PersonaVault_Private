import os
import socket
import logging
import httpx
from typing import Optional, Tuple, List, Dict
from app.swarm.routing.complexity_detector import ComplexityDetector
from app.services.intelligence_gateway import gateway

logger = logging.getLogger(__name__)

class ReasoningRouter:
    """Routes queries to appropriate reasoning provider based on sovereignty rules"""
    
    # Provider ranking (fast → deep reasoning)
    PROVIDER_HIERARCHY = {
        "fast": ["groq/mixtral-8x7b-32768", "ollama/tinydolphin:latest"],
        "reasoning": ["groq/qwen-qwq-32b", "ollama/qwen-reasoning"],
    }
    
    def __init__(self):
        self.airgapped = self._detect_airgapped()
        self.local_only = os.getenv("PERSONA_VAULT_MODE") == "airgap"
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.detector = ComplexityDetector()
    
    def _get_configured_model(self, provider: str, default_model: str) -> str:
        """Helper to get configured model from gateway or fallback."""
        provider_config = gateway.ai_tool.providers.get(provider.lower(), {})
        return provider_config.get("model", default_model)

    async def route(self, query: str, context: Optional[List[Dict]] = None) -> Tuple[str, Dict]:
        """
        Returns: (provider, route_metadata)
        """
        # 1. Assess complexity
        complexity = await self.detector.assess_complexity(query, context or [])
        
        # 2. Discover available providers (dynamic check)
        available = await self._discover_providers()
        
        # 3. Determine if we need reasoning
        if complexity["needs_reasoning"]:
            return await self._route_reasoning(available, complexity)
        else:
            return await self._route_fast(available, complexity)
    
    async def _route_reasoning(self, available: List[str], complexity: Dict) -> Tuple[str, Dict]:
        """Route to reasoning-capable model"""
        
        # Check airgapped or local-only constraints
        if self.airgapped or self.local_only:
            if "ollama/qwen-reasoning" in available:
                return "ollama", {
                    "model": self._get_configured_model("ollama", "qwen-reasoning"),
                    "mode": "reasoning",
                    "reason": "Air-gapped: using local reasoning model",
                    "complexity": complexity
                }
            return "ollama", {
                "model": self._get_configured_model("ollama", os.getenv("OLLAMA_LLM_MODEL", "tinydolphin:latest")),
                "mode": "fallback",
                "reason": "Air-gapped: no local reasoning model found, falling back",
                "complexity": complexity
            }
        
        # Cloud available
        if "groq/qwen-qwq-32b" in available:
            return "groq", {
                "model": self._get_configured_model("groq", "qwen/qwen3.6-27b"),
                "mode": "reasoning",
                "reason": f"High complexity ({complexity['score']:.2f}): using Groq reasoning",
                "complexity": complexity
            }
        
        return "groq", {
            "model": self._get_configured_model("groq", "qwen/qwen3.6-27b"),
            "mode": "default",
            "reason": "Groq available, using default model",
            "complexity": complexity
        }
    
    async def _route_fast(self, available: List[str], complexity: Dict) -> Tuple[str, Dict]:
        """Route to fast model for simple queries"""
        
        if self.airgapped or self.local_only:
            return "ollama", {
                "model": self._get_configured_model("ollama", os.getenv("OLLAMA_LLM_MODEL", "tinydolphin:latest")),
                "mode": "fast",
                "reason": "Air-gapped: using fast local model",
                "complexity": complexity
            }
        
        return "groq", {
            "model": self._get_configured_model("groq", "qwen/qwen3.6-27b"),
            "mode": "fast",
            "reason": f"Low complexity ({complexity['score']:.2f}): using Groq",
            "complexity": complexity
        }
    
    def _detect_airgapped(self) -> bool:
        """Detect if running in air-gapped environment"""
        try:
            # Try to connect to a common public DNS
            socket.create_connection(("8.8.8.8", 53), timeout=1.0)
            return False
        except (OSError, socket.timeout):
            return True
    
    async def _discover_providers(self) -> List[str]:
        """Discover available model providers"""
        providers = []
        
        # Check Ollama
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self.ollama_url}/api/tags")
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    for m in models:
                        name = m.get("name", "")
                        providers.append(f"ollama/{name}")
        except Exception:
            pass
            
        # Check Groq
        if not self.airgapped and os.getenv("GROQ_API_KEY"):
            providers.extend(["groq/mixtral-8x7b-32768", "groq/qwen-qwq-32b"])
            
        return providers
