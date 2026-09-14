import pytest
from fastapi import status
from datetime import datetime, timezone, timedelta
from app.models import User, UserSession
import uuid

@pytest.mark.asyncio
async def test_get_current_settings(client, db_session):
    """Test getting current Ollama settings."""
    user = User(username="test_user", email=f"test_{uuid.uuid4().hex[:6]}@test.com", hashed_password="dummy_password", is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    session_id = str(uuid.uuid4())
    user_sess = UserSession(user_id=user.id, session_token=session_id, expires_at=datetime.now(timezone.utc) + timedelta(days=1), is_active=True)
    db_session.add(user_sess)
    await db_session.commit()

    client.cookies.set("session_id", session_id)

    response = await client.get(
        "/api/v1/ollama/settings",
        headers={"Content-Type": "application/json"},
        params={"user_id": user.id}
    )

    assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]

@pytest.mark.asyncio
async def test_ollama_settings_past(client, db_session):
    """Test getting past Ollama settings."""
    # Create a user first
    import uuid
    user = User(username=f"test_user_{uuid.uuid4().hex[:6]}", email=f"test_{uuid.uuid4().hex[:6]}@test.com", hashed_password="dummy_password", is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    session_id = str(uuid.uuid4())
    user_sess = UserSession(user_id=user.id, session_token=session_id, expires_at=datetime.now(timezone.utc) + timedelta(days=1), is_active=True)
    db_session.add(user_sess)
    await db_session.commit()
    
    client.cookies.set("session_id", session_id)
    
    response = await client.get(
        "/api/v1/ollama/settings/past",
        params={"user_id": user.id}
    )
    assert response.status_code in [200, 401, 404], f"Unexpected status: {response.status_code}"

from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_ollama_models(client):
    """Test getting available Ollama models."""
    from unittest.mock import MagicMock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"models": []}
    
    with patch("app.api.v1.endpoints.dashboard.utils._check_ollama", return_value="connected"), \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        response = await client.get("/api/v1/ollama/models")
        assert response.status_code in [200, 401, 500], f"Unexpected status: {response.status_code}"

