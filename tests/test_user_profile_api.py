import pytest
from app.models import UserProfile

@pytest.mark.asyncio
async def test_get_user_profile_endpoint(admin_client, db_session):
    # Get profile (should 404 first time)
    response = admin_client.get("/api/v1/user-profile/me")
    assert response.status_code == 404
    
    # Create profile
    payload = {"active_persona": "clinical_expert", "preferences": {"theme": "dark"}}
    response = admin_client.post("/api/v1/user-profile/me", json=payload)
    assert response.status_code == 200
    
    # Get again (should 200)
    response = admin_client.get("/api/v1/user-profile/me")
    assert response.status_code == 200
    assert response.json()["active_persona"] == "clinical_expert"
    assert response.json()["preferences"]["theme"] == "dark"
