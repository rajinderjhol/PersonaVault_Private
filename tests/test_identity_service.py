"""
Identity Service Tests - Full test suite for the identity layer
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
import shutil

from app.services.identity.identity_service import IdentityService
from app.models.identity import (
    DeviceType, DeviceTrustLevel, PermissionLevel
)


@pytest.fixture
def service():
    """Create a fresh IdentityService instance for each test and clean up after."""
    import os
    test_data_path = Path("data_test")
    
    # Helper to clean test files
    def cleanup():
        for file in test_data_path.glob("*.json"):
            if file.exists():
                file.unlink()

    cleanup()
    
    service = IdentityService()
    service.data_path = test_data_path
    service.data_path.mkdir(parents=True, exist_ok=True)
    service._load_data()

    yield service
    
    cleanup()


@pytest.fixture
def test_user():
    """Create a test user."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User"
    }


@pytest.mark.asyncio
async def test_create_profile(service, test_user):
    """Test creating a user profile."""
    profile = await service.create_profile(
        username=test_user["username"],
        email=test_user["email"],
        full_name=test_user["full_name"]
    )
    
    assert profile.id is not None
    assert profile.username == test_user["username"]


@pytest.mark.asyncio
async def test_get_profile(service, test_user):
    """Test retrieving a user profile."""
    created = await service.create_profile(
        username=test_user["username"],
        email=test_user["email"]
    )
    
    retrieved = await service.get_profile(created.id)
    assert retrieved is not None
    assert retrieved.id == created.id


@pytest.mark.asyncio
async def test_update_profile(service, test_user):
    """Test updating a user profile."""
    created = await service.create_profile(
        username=test_user["username"],
        email=test_user["email"]
    )
    
    updated = await service.update_profile(
        created.id,
        full_name="Updated Name"
    )
    
    assert updated.full_name == "Updated Name"


@pytest.mark.asyncio
async def test_register_device(service):
    """Test registering a device."""
    device = await service.register_device(
        user_id=1,
        name="Test Laptop",
        device_type=DeviceType.DESKTOP
    )
    
    assert device.id is not None
    assert device.name == "Test Laptop"


@pytest.mark.asyncio
async def test_get_devices(service):
    """Test retrieving devices for a user."""
    for i in range(3):
        await service.register_device(
            user_id=1,
            name=f"Device {i+1}",
            device_type=DeviceType.WEB
        )
    
    retrieved = await service.get_devices(1)
    assert len(retrieved) == 3


@pytest.mark.asyncio
async def test_grant_permission(service):
    """Test granting a permission."""
    permission = await service.grant_permission(
        user_id=1,
        action="read_documents",
        level=PermissionLevel.EXECUTE
    )
    
    assert permission.action == "read_documents"
    assert permission.level == PermissionLevel.EXECUTE


@pytest.mark.asyncio
async def test_check_permission(service):
    """Test checking permissions."""
    await service.grant_permission(
        user_id=1,
        action="read_documents",
        level=PermissionLevel.EXECUTE
    )
    
    assert await service.check_permission(1, "read_documents", PermissionLevel.EXECUTE) is True
    assert await service.check_permission(1, "read_documents", PermissionLevel.AUTONOMOUS) is False


@pytest.mark.asyncio
async def test_add_trusted_entity(service):
    """Test adding a trusted entity."""
    entity = await service.add_trusted_entity(
        user_id=1,
        entity_type="device",
        entity_id="dev_123",
        trust_level=0.8
    )
    
    assert entity.entity_id == "dev_123"
    assert entity.trust_level == 0.8


@pytest.mark.asyncio
async def test_sync_state(service):
    """Test sync state."""
    state = await service.update_sync_state(
        user_id=1,
        device_id="dev_1",
        sync_version="2.0.0"
    )
    assert state.sync_version == "2.0.0"
