import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PhaseService:
    def __init__(self):
        self.gas_memory = []
        self.liquid_memory = []
        self.ice_patterns = []
        self.snowflakes = []

    async def get_gas(self, env_id: str) -> List[Dict[str, Any]]:
        """Get working memory (Gas phase)."""
        # Return active working memory
        return [m for m in self.gas_memory if m.get("env_id") == env_id]

    async def get_liquid(self, env_id: str) -> List[Dict[str, Any]]:
        """Get episodic memory (Liquid phase)."""
        return [m for m in self.liquid_memory if m.get("env_id") == env_id]

    async def get_snowflakes(self, env_id: str, pack_ids: List[str]) -> List[Dict[str, Any]]:
        """Get domain-specific patterns (Snowflakes)."""
        return [s for s in self.snowflakes 
                if s.get("env_id") == env_id and s.get("pack_id") in pack_ids]

    async def add_to_gas(self, env_id: str, item: Dict[str, Any]) -> None:
        """Add to working memory."""
        item["env_id"] = env_id
        item["timestamp"] = datetime.utcnow().isoformat()
        self.gas_memory.append(item)

    async def promote_to_liquid(self, env_id: str, item_id: str) -> None:
        """Promote from Gas to Liquid."""
        # Find in gas and move to liquid
        for i, item in enumerate(self.gas_memory):
            if item.get("id") == item_id and item.get("env_id") == env_id:
                self.liquid_memory.append(item)
                del self.gas_memory[i]
                break

    async def crystallize_to_ice(self, env_id: str, pattern: Dict[str, Any]) -> None:
        """Add a crystallized pattern to Ice."""
        pattern["env_id"] = env_id
        pattern["crystallized_at"] = datetime.utcnow().isoformat()
        self.ice_patterns.append(pattern)