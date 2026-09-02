from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.reasoning_chain import ReasoningChainModel
from app.repositories.sqlalchemy.base import SQLBaseRepository
from sqlalchemy import select, desc

class ReasoningChainRepository(SQLBaseRepository):
    """Repository for reasoning chain storage and retrieval."""
    
    def __init__(self, db):
        super().__init__(db)
        self.model = ReasoningChainModel
    
    async def get_chain(self, chain_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a reasoning chain by ID."""
        session = await self._get_session()
        try:
            query = select(self.model).where(self.model.id == chain_id)
            result = await session.execute(query)
            chain = result.scalar_one_or_none()
            if chain:
                return chain.to_dict()
            return None
        finally:
            await self._close_session(session)
    
    async def get_chains_for_goal(self, goal_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve all reasoning chains for a specific goal."""
        session = await self._get_session()
        try:
            query = select(self.model).where(self.model.goal_id == goal_id).order_by(desc(self.model.created_at)).limit(limit)
            result = await session.execute(query)
            chains = result.scalars().all()
            return [chain.to_dict() for chain in chains]
        finally:
            await self._close_session(session)
    
    async def get_chains_for_environment(self, environment_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve all reasoning chains for an environment."""
        session = await self._get_session()
        try:
            query = select(self.model).where(self.model.environment_id == environment_id).order_by(desc(self.model.created_at)).limit(limit)
            result = await session.execute(query)
            chains = result.scalars().all()
            return [chain.to_dict() for chain in chains]
        finally:
            await self._close_session(session)
    
    async def get_chains_by_date_range(self, start_date: datetime, end_date: datetime, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve reasoning chains within a date range."""
        session = await self._get_session()
        try:
            query = select(self.model).where(
                self.model.created_at >= start_date,
                self.model.created_at <= end_date
            ).order_by(desc(self.model.created_at)).limit(limit)
            result = await session.execute(query)
            chains = result.scalars().all()
            return [chain.to_dict() for chain in chains]
        finally:
            await self._close_session(session)
    
    async def save_chain(self, chain_data: Dict[str, Any]) -> str:
        """Save a reasoning chain."""
        session = await self._get_session()
        try:
            chain = self.model(**chain_data)
            session.add(chain)
            await session.commit()
            await session.refresh(chain)
            return chain.id
        finally:
            await self._close_session(session)
