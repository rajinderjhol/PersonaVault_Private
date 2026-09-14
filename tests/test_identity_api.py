import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_create_profile(client):
    """Test POST /api/v1/identity/profile"""
    response = await client.post(
        "/api/v1/identity/profile",
        json={
            "username": "apitestuser",
            "email": "api@test.com",
            "full_name": "API Test User"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "apitestuser"
    assert data["id"] is not None

@pytest.mark.asyncio
async def test_get_profile(client):
    """Test GET /api/v1/identity/profile/{user_id}"""
    create_response = await client.post(
        "/api/v1/identity/profile",
        json={
            "username": "gettestuser",
            "email": "get@test.com",
            "full_name": "Get Test User"
        }
    )
    user_id = create_response.json()["id"]
    
    response = await client.get(f"/api/v1/identity/profile/{user_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id

@pytest.mark.asyncio
async def test_register_device(client):
    """Test POST /api/v1/identity/device/{user_id}"""
    user_response = await client.post(
        "/api/v1/identity/profile",
        json={
            "username": "devicetestuser",
            "email": "device@test.com"
        }
    )
    user_id = user_response.json()["id"]
    
    response = await client.post(
        f"/api/v1/identity/device/{user_id}",
        json={
            "name": "API Test Device",
            "device_type": "web"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert data["name"] == "API Test Device"

@pytest.mark.asyncio
async def test_grant_permission(client):
    """Test POST /api/v1/identity/permission/{user_id}"""
    user_response = await client.post(
        "/api/v1/identity/profile",
        json={
            "username": "permissiontestuser",
            "email": "permission@test.com"
        }
    )
    user_id = user_response.json()["id"]
    
    response = await client.post(
        f"/api/v1/identity/permission/{user_id}",
        json={
            "action": "read_documents",
            "level": "execute"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "read_documents"
    assert data["level"] == "execute"

@pytest.mark.asyncio
async def test_check_permission(client):
    """Test GET /api/v1/identity/permission/{user_id}/check"""
    user_response = await client.post(
        "/api/v1/identity/profile",
        json={
            "username": "checktestuser",
            "email": "check@test.com"
        }
    )
    user_id = user_response.json()["id"]
    
    await client.post(
        f"/api/v1/identity/permission/{user_id}",
        json={
            "action": "read_documents",
            "level": "execute"
        }
    )
    
    # Check pass
    response = await client.get(
        f"/api/v1/identity/permission/{user_id}/check",
        params={
            "action": "read_documents",
            "level": "execute"
        }
    )
    assert response.status_code == 200
    assert response.json()["has_permission"] is True
    
    # Check fail
    response = await client.get(
        f"/api/v1/identity/permission/{user_id}/check",
        params={
            "action": "read_documents",
            "level": "autonomous"
        }
    )
    assert response.status_code == 200
    assert response.json()["has_permission"] is False

@pytest.mark.asyncio
async def test_add_trusted_entity(client):
    """Test POST /api/v1/identity/trust/{user_id}"""
    user_response = await client.post(
        "/api/v1/identity/profile",
        json={
            "username": "trusttestuser",
            "email": "trust@test.com"
        }
    )
    user_id = user_response.json()["id"]
    
    response = await client.post(
        f"/api/v1/identity/trust/{user_id}",
        json={
            "entity_type": "device",
            "entity_id": "trusted_device_123",
            "trust_level": 0.9,
            "reason": "Test trusted device"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["trust_level"] == 0.9
