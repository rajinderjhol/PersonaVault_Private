from typing import List, Any
from app.repositories.interfaces import IEpisodicTaskRepository

class EpisodicMemory:
    """Task histories for learning patterns. Orchestrates task history storage."""
    
    def __init__(self, repository: IEpisodicTaskRepository):
        self.repository = repository
    
    async def store(self, entry: Any):
        """Store an episodic task entry via the repository."""
        return await self.repository.store(entry)

    async def get_recent(self, limit: int = 10):
        """Get recent episodic task entries via the repository."""
        return await self.repository.get_recent(limit)