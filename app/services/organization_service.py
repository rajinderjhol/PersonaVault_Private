from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.organization_repository import OrganizationRepository
from app.models.organization import Organization
from fastapi import HTTPException

class OrganizationService:
    def __init__(self, db: AsyncSession):
        self.repo = OrganizationRepository(db)

    async def create_organization(self, name: str, slug: str, description: str = None) -> Organization:
        existing = await self.repo.get_by_slug(slug)
        if existing:
            raise HTTPException(status_code=400, detail="Organization with this slug already exists")
        return await self.repo.create(name=name, slug=slug, description=description)

    async def get_organization(self, org_id: int) -> Organization:
        org = await self.repo.get_by_id(org_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        return org
