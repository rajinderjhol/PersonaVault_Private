import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CrystallizationService:
    """Service for crystallizing reasoning patterns into Ice memory."""
    
    def __init__(self):
        self.patterns = []
    
    async def crystallize(
        self,
        env_id: str,
        pattern: Dict[str, Any],
        source: str = "chat_reasoning"
    ) -> Dict[str, Any]:
        """
        Crystallize a reasoning pattern into Ice memory.
        
        Args:
            env_id: The environment ID
            pattern: The pattern to crystallize (contains query, reasoning, etc.)
            source: The source of the pattern
        
        Returns:
            Dictionary with pattern_id and status
        """
        pattern_id = f"PAT-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{len(self.patterns) + 1}"
        
        self.patterns.append({
            "pattern_id": pattern_id,
            "env_id": env_id,
            "source": source,
            "pattern": pattern,
            "created_at": datetime.now().isoformat()
        })
        
        logger.info(f"✅ Crystallized pattern: {pattern_id} for env: {env_id}")
        
        return {
            "pattern_id": pattern_id,
            "status": "crystallized",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_patterns(self, env_id: str) -> list:
        """Get all crystallized patterns for an environment."""
        return [p for p in self.patterns if p.get("env_id") == env_id]
    
    async def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific pattern by ID."""
        for p in self.patterns:
            if p.get("pattern_id") == pattern_id:
                return p
        return None

# Create a singleton instance
crystallization_service = CrystallizationService()
