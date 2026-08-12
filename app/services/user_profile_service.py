from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_profile_repository import UserProfileRepository
from app.models.user_profile import UserProfile
from fastapi import HTTPException

class UserProfileService:
    def __init__(self, db: AsyncSession):
        self.repo = UserProfileRepository(db)

    async def get_profile(self, user_id: int) -> UserProfile:
        profile = await self.repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile

    async def create_or_update_profile(self, user_id: int, preferences: dict = None, active_persona: str = "default", workspace_config: dict = None) -> UserProfile:
        # Check if exists
        profile = await self.repo.get_by_user_id(user_id)
        if profile:
            # Update logic
            if preferences is not None: profile.preferences = preferences
            if active_persona: profile.active_persona = active_persona
            if workspace_config is not None: profile.workspace_config = workspace_config
            await self.repo.db.commit()
            await self.repo.db.refresh(profile)
            return profile
        else:
            # Create logic
            return await self.repo.create(user_id=user_id, preferences=preferences, active_persona=active_persona)
