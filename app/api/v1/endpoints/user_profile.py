from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.user_profile_service import UserProfileService
from app.schemas.user_profile import UserProfileCreate, UserProfileResponse
from app.core.dependencies import get_current_user
from app.models import User

router = APIRouter(prefix="/user-profile", tags=["user-profile"])

@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = UserProfileService(db)
    return await service.get_profile(current_user.id)

@router.post("/me", response_model=UserProfileResponse)
async def update_my_profile(
    profile_in: UserProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = UserProfileService(db)
    return await service.create_or_update_profile(
        user_id=current_user.id,
        preferences=profile_in.preferences,
        active_persona=profile_in.active_persona,
        workspace_config=profile_in.workspace_config
    )
