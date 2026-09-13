
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.v1.endpoints.thermodynamics import router

# Create a minimal app for testing thermodynamics routes
app = FastAPI()
app.include_router(router)
client = TestClient(app)

def test_thermodynamics_endpoints():
    """Test thermodynamics API endpoints in isolation."""
    # Test Phase Distribution
    response = client.get("/api/v1/thermodynamics/phase-distribution")
    assert response.status_code == 200
    assert "gas" in response.json()

    # Test Transitions
    response = client.get("/api/v1/thermodynamics/transitions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Test Snowflakes
    response = client.get("/api/v1/thermodynamics/snowflakes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Test Branching
    valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
    response = client.post(f"/api/v1/thermodynamics/snowflakes/{valid_uuid}/branch/security")
    # This might fail with 404 (not found), which is fine, but it should not be 400.
    assert response.status_code != 400
