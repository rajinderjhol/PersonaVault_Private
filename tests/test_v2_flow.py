import pytest
from app.main import app

# Use the 'client' fixture from conftest.py which provides admin authentication and DB session
def test_v2_environment_lifecycle(client):
    # 1. Create Environment
    response = client.post("/v2/environments/", json={
        "name": "Integration Test Env",
        "owner_principal_id": "test-user-1",
        "type": "standard"
    })
    assert response.status_code == 200
    env = response.json()
    env_id = env["id"]

    # 2. List Environments
    response = client.get("/v2/environments/")
    assert response.status_code == 200
    assert len(response.json()) >= 1

    # 3. Get Environment
    response = client.get(f"/v2/environments/{env_id}")
    assert response.status_code == 200
    assert response.json()["id"] == env_id

    # 4. List Adapted Packs (Should return successfully)
    response = client.get(f"/v2/environments/{env_id}/packs/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # 5. Add Member
    response = client.post(f"/v2/environments/{env_id}/members/", json={
        "principal_id": "test-user-2",
        "role": "analyst",
        "permissions": ["read:memory"]
    })
    assert response.status_code == 200
    member = response.json()
    assert member["principal_id"] == "test-user-2"

    # 6. List Members
    response = client.get(f"/v2/environments/{env_id}/members/")
    assert response.status_code == 200
    assert len(response.json()) == 2

    # 7. Grant Authority
    response = client.post(f"/v2/environments/{env_id}/authorities/", json={
        "principal_id": "test-user-2",
        "capability": "execute_query"
    })
    assert response.status_code == 200
    grant = response.json()
    assert grant["capability"] == "execute_query"
