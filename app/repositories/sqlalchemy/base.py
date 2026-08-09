from typing import Any, Union
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

class SQLBaseRepository:
    """Base class for SQLAlchemy repositories handling session management."""
    
    def __init__(self, db: Union[AsyncSession, async_sessionmaker[AsyncSession]]):
        self.db = db

    async def _get_session(self) -> AsyncSession:
        """Helper to get an active session."""
        if callable(self.db):
            return self.db()
        return self.db

    async def _close_session(self, session: AsyncSession):
        """Helper to close session if it was factory-created."""
        if callable(self.db):
            await session.close()
