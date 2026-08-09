"""
Tests for the Admin Dashboard endpoints.
Uses the `admin_client` fixture which is pre-authenticated as an admin user.
"""
import pytest
from fastapi import status


async def test_get_admin_metrics(admin_client):
    """Test the comprehensive metrics endpoint returns expected structure."""
    response = admin_client.get("/api/v1/admin/dashboard/metrics")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "users" in data
    assert "memories" in data
    assert "system" in data
    assert "storage_used" in data["system"]


async def test_list_users_admin(admin_client):
    """Test the admin user list endpoint returns paginated users."""
    response = admin_client.get("/api/v1/admin/dashboard/users")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total" in data
    assert "users" in data
    assert len(data["users"]) >= 1


async def test_admin_endpoint_requires_auth(client):
    """Admin endpoints must return 401/403 for unauthenticated requests."""
    response = client.get("/api/v1/admin/dashboard/metrics")
    assert response.status_code in [
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ]


async def test_admin_endpoint_requires_admin_role(auth_client):
    """Regular users must be forbidden from admin endpoints."""
    response = auth_client.get("/api/v1/admin/dashboard/metrics")
    assert response.status_code == status.HTTP_403_FORBIDDEN
