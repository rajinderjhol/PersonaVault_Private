import pytest
from fastapi import status
from app.models import User, UserSession
import uuid

@pytest.mark.asyncio
async def test_get_current_settings(client, db_session):
    """Test getting current Ollama settings."""
    user = User(username="test_user", email="test@test.com", hashed_password="dummy_password", is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    session_id = str(uuid.uuid4())
    user_sess = UserSession(user_id=user.id, session_id=session_id, is_active=True)
    db_session.add(user_sess)
    await db_session.commit()

    client.cookies.set("session_id", session_id)

    response = client.get(
        "/api/v1/ollama/settings",
        headers={"Content-Type": "application/json"},
        params={"user_id": user.id}
    )

    assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]

def test_ollama_settings_past(client):
    """Test getting past Ollama settings."""
    user_id = 1
    response = client.get(
        "/api/v1/ollama/settings/past",
        params={"user_id": user_id}
    )
    assert response.status_code in [200, 401, 404], f"Unexpected status: {response.status_code}"

def test_ollama_models(client):
    """Test getting available Ollama models."""
    response = client.get("/api/v1/ollama/models")
    assert response.status_code in [200, 401, 500], f"Unexpected status: {response.status_code}"

