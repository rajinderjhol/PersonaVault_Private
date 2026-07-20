import pytest
from fastapi import status
from app.models import User, UserSession
import uuid

@pytest.fixture
def admin_client(client, session):
    """Fixture to provide a client authenticated as an admin."""
    user = User(username="admin_test", email="admin@test.com", role="admin", is_active=True)
    session.add(user)
    session.commit()
    
    session_id = str(uuid.uuid4())
    db_session = UserSession(user_id=user.id, session_id=session_id, is_active=True)
    session.add(db_session)
    session.commit()
    
    client.cookies.set("session_id", session_id)
    return client

def test_get_admin_metrics(admin_client):
    """Test the comprehensive metrics endpoint."""
    response = admin_client.get("/api/v1/admin/dashboard/metrics")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "users" in data
    assert "memories" in data
    assert "system" in data
    assert "storage_used" in data["system"]

def test_list_users_admin(admin_client):
    """Test the admin user list endpoint."""
    response = admin_client.get("/api/v1/admin/dashboard/users")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total" in data
    assert "users" in data
    assert len(data["users"]) >= 1