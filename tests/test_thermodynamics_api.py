import pytest
from fastapi import status

def test_get_phase_distribution(client):
    """Test getting thermodynamic phase distribution."""
    response = client.get("/api/v1/thermodynamics/phase-distribution")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "gas" in data
    assert "liquid" in data
    assert "ice" in data
    assert "snowflake" in data

def test_get_transitions(client):
    """Test getting recent transitions."""
    response = client.get("/api/v1/thermodynamics/transitions")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)

def test_get_snowflakes(client):
    """Test listing snowflake variants."""
    response = client.get("/api/v1/thermodynamics/snowflakes")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)

def test_branch_snowflake(client):
    """Test branching a pattern to a snowflake."""
    response = client.post("/api/v1/thermodynamics/snowflakes/p_base_001/branch/security")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "success"
