import pytest
from models import User, Memory, Organization

def test_create_user_model():
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        role="user"
    )
    assert user.username == "testuser"
    assert user.role == "user"

def test_create_organization_model():
    org = Organization(
        name="Test Org",
        slug="test-org",
        subscription_tier="pro"
    )
    assert org.name == "Test Org"
    assert org.is_active == True