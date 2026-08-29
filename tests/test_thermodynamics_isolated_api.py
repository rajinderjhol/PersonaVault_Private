
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
    response = client.post("/api/v1/thermodynamics/snowflakes/p_base_001/branch/security")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
