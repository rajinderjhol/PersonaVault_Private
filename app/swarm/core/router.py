import logging
from typing import Dict, Any
from app.config import Config

logger = logging.getLogger(__name__)

class AIRouter:
    """
    Intelligent AI Routing Service for PersonaVault.
    Handles routing between local (Ollama) and cloud (Gemini) providers based on:
    - Engine Mode (Local-First vs Hybrid)
    - Data Sensitivity (Privacy constraints)
    - Task Complexity (Reasoning requirements)
    - Air-Gapped Constraints
    """
    def __init__(self, engine_mode: str):
        self.engine_mode = engine_mode # Detected on startup

    async def get_route(self, query: str, complexity: float = 0.5, sensitivity: str = "medium") -> Dict[str, Any]:
        """
        Determines the optimal intelligence provider for a given query.
        """
        # Default to local (Privacy-First principle)
        provider = "ollama"
        tier = "local"

        # 1. Air-Gapped / Security Check: Strictly block cloud if air-gapped or Local-First mode.
        if Config.IS_AIR_GAPPED or "Local-First" in self.engine_mode:
             if Config.IS_AIR_GAPPED:
                 logger.debug("AIRouter: System is air-gapped. Cloud routing strictly disabled.")
             provider = "ollama"
             tier = "local"
        
        # 2. Privacy Policy Override: High sensitivity data MUST stay local.
        elif sensitivity.lower() == "high":
            logger.info("AIRouter: Routing to local engine due to high data sensitivity.")
            provider = "ollama"
            tier = "local"
        
        # 3. Hybrid Reasoning: Route complex tasks to cloud models if local can't handle it.
        elif "Hybrid" in self.engine_mode and complexity > 0.7:
            logger.info(f"AIRouter: Routing to cloud (Gemini) for complex reasoning (score: {complexity}).")
            provider = "gemini"
            tier = "cloud"
            
        # 4. Air-Gapped / Enterprise constraint check
        # (Future: Logic for secure enterprise-gapped cloud endpoints like Azure Govt/AWS TopSecret)

        return {
            "provider": provider,
            "tier": tier,
            "mode": self.engine_mode
        }