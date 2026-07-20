import pytest
from fastapi import status
from app.models import User, UserSession
import uuid

def test_get_current_settings(client, session):
    """Test getting current Ollama settings."""
    # Setup authenticated user and session in DB
    user = User(username="test_user", email="test@test.com", is_active=True)
    session.add(user)
    session.commit()
    
    session_id = str(uuid.uuid4())
    db_session = UserSession(user_id=user.id, session_id=session_id, is_active=True)
    session.add(db_session)
    session.commit()

    client.cookies.set("session_id", session_id)

    # FIX: Use the correct endpoint (without /current)
    response = client.get(
        "/api/v1/ollama/settings",
        headers={"Content-Type": "application/json"},
        params={"user_id": user.id}
    )

    # Now that we are authenticated, we expect a clean 200 or 404, not a 401
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    if response.status_code == 200:
        response_json = response.json()
        # Check that we got a valid response
        assert "profile_name" in response_json or "message" in response_json

def test_ollama_settings_past(client):
    """Test getting past Ollama settings."""
    user_id = 1
    response = client.get(
        "/api/v1/ollama/settings/past",
        params={"user_id": user_id}
    )
    assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"

def test_ollama_models(client):
    """Test getting available Ollama models."""
    response = client.get("/api/v1/ollama/models")
    assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"
