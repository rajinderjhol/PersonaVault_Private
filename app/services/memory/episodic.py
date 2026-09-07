import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class EpisodicMemoryService:
    def __init__(self):
        self.episodes = []

    async def store(
        self,
        env_id: str,
        event_type: str,
        query: str,
        trace: Dict[str, Any],
        timestamp: str
    ) -> Dict[str, Any]:
        """Store an episodic memory."""
        episode = {
            "id": f"ep_{len(self.episodes) + 1}",
            "env_id": env_id,
            "type": event_type,
            "query": query,
            "trace": trace,
            "timestamp": timestamp,
            "created_at": datetime.utcnow().isoformat()
        }
        self.episodes.append(episode)
        logger.info(f"Stored episode {episode['id']} for {env_id}")
        return {"status": "stored", "id": episode["id"]}

    async def get_episodes(self, env_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent episodes for an environment."""
        episodes = [e for e in self.episodes if e["env_id"] == env_id]
        return episodes[-limit:] if episodes else []