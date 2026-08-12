import pytest
import uuid
from app.models import Organization

@pytest.mark.asyncio
async def test_create_organization_endpoint(admin_client):
    """Test creating an organization via API."""
    payload = {
        "name": f"Test Org {uuid.uuid4().hex[:6]}",
        "slug": f"test-org-{uuid.uuid4().hex[:6]}",
        "description": "API Test Organization"
    }
    
    response = admin_client.post("/api/v1/organizations/", json=payload)
    
    # Check that we get 201 (created)
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == payload["name"]
    assert "id" in data

@pytest.mark.asyncio
async def test_get_organization_endpoint(admin_client, db_session):
    """Test getting an organization via API."""
    # First create an organization directly in the database
    org = Organization(
        name=f"Get Test {uuid.uuid4().hex[:6]}",
        slug=f"get-org-{uuid.uuid4().hex[:6]}",
        description="Get Test Organization"
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    
    # Get it via API
    response = admin_client.get(f"/api/v1/organizations/{org.id}")
    
    # Should return 200
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == org.id
    assert data["name"] == org.name
