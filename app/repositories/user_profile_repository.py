from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user_profile import UserProfile
from typing import Optional

class UserProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int) -> Optional[UserProfile]:
        result = await self.db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        return result.scalars().first()

    async def create(self, user_id: int, preferences: dict = None, active_persona: str = "default") -> UserProfile:
        profile = UserProfile(user_id=user_id, preferences=preferences or {}, active_persona=active_persona)
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile
