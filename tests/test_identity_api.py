"""
Identity API Tests - Test the identity API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_profile():
    """Test POST /api/v1/identity/profile"""
    response = client.post(
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

def test_get_profile():
    """Test GET /api/v1/identity/profile/{user_id}"""
    create_response = client.post(
        "/api/v1/identity/profile",
        json={
            "username": "gettestuser",
            "email": "get@test.com",
            "full_name": "Get Test User"
        }
    )
    user_id = create_response.json()["id"]
    
    response = client.get(f"/api/v1/identity/profile/{user_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id

def test_register_device():
    """Test POST /api/v1/identity/device/{user_id}"""
    user_response = client.post(
        "/api/v1/identity/profile",
        json={
            "username": "devicetestuser",
            "email": "device@test.com"
        }
    )
    user_id = user_response.json()["id"]
    
    response = client.post(
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

def test_grant_permission():
    """Test POST /api/v1/identity/permission/{user_id}"""
    user_response = client.post(
        "/api/v1/identity/profile",
        json={
            "username": "permissiontestuser",
            "email": "permission@test.com"
        }
    )
    user_id = user_response.json()["id"]
    
    response = client.post(
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

def test_check_permission():
    """Test GET /api/v1/identity/permission/{user_id}/check"""
    user_response = client.post(
        "/api/v1/identity/profile",
        json={
            "username": "checktestuser",
            "email": "check@test.com"
        }
    )
    user_id = user_response.json()["id"]
    
    client.post(
        f"/api/v1/identity/permission/{user_id}",
        json={
            "action": "read_documents",
            "level": "execute"
        }
    )
    
    # Check pass
    response = client.get(
        f"/api/v1/identity/permission/{user_id}/check",
        params={
            "action": "read_documents",
            "level": "execute"
        }
    )
    assert response.status_code == 200
    assert response.json()["has_permission"] is True
    
    # Check fail
    response = client.get(
        f"/api/v1/identity/permission/{user_id}/check",
        params={
            "action": "read_documents",
            "level": "autonomous"
        }
    )
    assert response.status_code == 200
    assert response.json()["has_permission"] is False

def test_add_trusted_entity():
    """Test POST /api/v1/identity/trust/{user_id}"""
    user_response = client.post(
        "/api/v1/identity/profile",
        json={
            "username": "trusttestuser",
            "email": "trust@test.com"
        }
    )
    user_id = user_response.json()["id"]
    
    response = client.post(
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
