from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.organization_service import OrganizationService
from app.schemas.organization import OrganizationCreate, OrganizationResponse
from typing import List

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_in: OrganizationCreate,
    db: AsyncSession = Depends(get_db)
):
    service = OrganizationService(db)
    return await service.create_organization(
        name=org_in.name, 
        slug=org_in.slug, 
        description=org_in.description
    )

@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = OrganizationService(db)
    return await service.get_organization(org_id)
