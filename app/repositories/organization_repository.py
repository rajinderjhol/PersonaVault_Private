from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.organization import Organization
from typing import List, Optional

class OrganizationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str, slug: str, description: str = None) -> Organization:
        org = Organization(name=name, slug=slug, description=description)
        self.db.add(org)
        await self.db.commit()
        await self.db.refresh(org)
        return org

    async def get_by_id(self, org_id: int) -> Optional[Organization]:
        result = await self.db.execute(select(Organization).where(Organization.id == org_id))
        return result.scalars().first()

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        result = await self.db.execute(select(Organization).where(Organization.slug == slug))
        return result.scalars().first()
