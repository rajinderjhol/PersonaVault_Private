import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_v2_health_endpoint():
    """Verify that the V2 health endpoint is accessible and returns the correct components."""
    response = client.get("/v2/health/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment_runtime" in data["components"]
    assert "governance_engine" in data["components"]
    assert "intelligence_runtime" in data["components"]
    
    print("\n✅ V2 Health Endpoint verified.")
