import pytest
from fastapi import status

@pytest.mark.asyncio
async def test_health_check(client):
    """Test the basic health endpoint."""
    response = await client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_readiness_check(client):
    """Test the database readiness probe."""
    response = await client.get("/health/readiness")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["database"] == "connected"