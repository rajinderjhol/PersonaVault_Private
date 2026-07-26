import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List

class CognitiveBlackboard:
    """
    Shared working memory (Layer 1 - Gas) for agent collaboration.
    Allows agents to post 'insights' and 'state changes' for others to observe.
    """
    def __init__(self):
        self.state: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def post_insight(self, agent_name: str, insight: Any, importance: float = 0.5):
        async with self._lock:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": agent_name,
                "data": insight,
                "importance": importance
            }
            self.state[agent_name] = entry
            self.history.append(entry)
            # Keep history manageable
            if len(self.history) > 100:
                self.history.pop(0)

    def get_snapshot(self) -> Dict[str, Any]:
        return {
            "current_state": self.state,
            "active_agents": list(self.state.keys())
        }