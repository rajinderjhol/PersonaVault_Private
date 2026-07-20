from fastapi import status

def test_health_check(client):
    """Test the basic health endpoint."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_readiness_check(client):
    """Test the database readiness probe."""
    response = client.get("/health/readiness")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["database"] == "connected"