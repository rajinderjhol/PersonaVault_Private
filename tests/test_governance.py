import pytest
from fastapi import status
from app.models import User, UserSession
from app.core.rate_limit import MAX_REQUESTS_PER_WINDOW, _rate_limit_store
import uuid

def test_rbac_public_access(client):
    """Verify that public paths are accessible without authentication."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK

def test_rbac_protected_access_denied(client):
    """Verify that protected API routes return 401 when no session is present."""
    response = client.get("/api/v1/memory/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_rbac_admin_restriction(client, session):
    """Verify that non-admin users cannot access admin prefixes."""
    # 1. Create a regular user and session
    user = User(username="regular_user", email="user@test.com", role="user", is_active=True)
    session.add(user)
    session.commit()
    
    session_id = str(uuid.uuid4())
    db_session = UserSession(user_id=user.id, session_id=session_id, is_active=True)
    session.add(db_session)
    session.commit()
    
    # 2. Set the cookie
    client.cookies.set("session_id", session_id)
    
    # 3. Attempt to access admin dashboard metrics
    response = client.get("/api/v1/admin/dashboard/metrics")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Admin privileges required" in response.json()["detail"]

def test_rate_limiting(client):
    """Verify that the rate limiter triggers after exceeding MAX_REQUESTS_PER_WINDOW."""
    # Clear the global store for this test
    _rate_limit_store.clear()
    
    endpoint = "/api/v1/auth/login"
    payload = {"username": "attacker", "password": "password"}
    
    # Hit the limit
    for _ in range(MAX_REQUESTS_PER_WINDOW):
        client.post(endpoint, json=payload)
        
    # The next one should be blocked
    response = client.post(endpoint, json=payload)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Too many requests" in response.json()["detail"]
    
    # Cleanup for other tests
    _rate_limit_store.clear()