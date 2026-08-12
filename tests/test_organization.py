import pytest
from app.services.organization_service import OrganizationService

@pytest.mark.asyncio
async def test_create_and_get_organization(db_session):
    service = OrganizationService(db_session)
    
    # Create
    org = await service.create_organization(name="Test Org", slug="test-org")
    assert org.id is not None
    assert org.name == "Test Org"
    
    # Get
    fetched = await service.get_organization(org.id)
    assert fetched.id == org.id
    assert fetched.slug == "test-org"

@pytest.mark.asyncio
async def test_create_duplicate_slug_fails(db_session):
    service = OrganizationService(db_session)
    await service.create_organization(name="Org 1", slug="dup")
    
    with pytest.raises(Exception): # FastAPI HTTPException
        await service.create_organization(name="Org 2", slug="dup")
