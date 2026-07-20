import logging
from datetime import datetime
from app.models import Memory
from app.services.memory_service import MemoryService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class HRIMemoryService:
    """
    Manages memory for human-robot interaction.
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.memory_service = MemoryService(db=db_session)

    async def store_interaction(self,
                               user_id: int,
                               robot_id: str,
                               interaction_text: str):
        """
        Store social interaction data linked to the user's primary memory vault.
        """
        # Create a new memory entry for the interaction
        new_memory = Memory(
            user_id=user_id,
            title=f"HRI with Robot {robot_id}",
            content=interaction_text,
            tags=f"hri,robot_{robot_id},social"
        )
        self.db.add(new_memory)
        await self.db.commit()
        await self.db.refresh(new_memory) # Ensure ID is loaded for indexing
        
        # Index the interaction for future recall during social encounters
        await self.memory_service.create_memory_entry(
            user_id, new_memory.title, new_memory.content, new_memory.tags, new_memory.id
        )
        return new_memory.id