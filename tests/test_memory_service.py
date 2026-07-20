import pytest
from datetime import datetime, timedelta
from app.models import Memory
from app.services.memory_service import MemoryService

def test_delete_expired_memories(session):
    """Test that expired memories are deleted and active ones remain."""
    memory_service = MemoryService(db=None, vector_service=None, graph_service=None) # Mock db later if needed
    
    # Create an expired memory (created 10 days ago with 5-day expiry)
    expired_memory = Memory(
        user_id=1,
        title="Expired Memory",
        content="This should be deleted",
        modality="text",
        created_at=datetime.utcnow() - timedelta(days=10),
        expiry_days=5
    )
    session.add(expired_memory)
    
    # Create an active memory (created today with 30-day expiry)
    active_memory = Memory(
        user_id=1,
        title="Active Memory",
        content="This memory should stay",
        modality="text",
        created_at=datetime.utcnow(),
        expiry_days=30
    )
    session.add(active_memory)
    
    # Create a memory with no expiry (should never be deleted)
    permanent_memory = Memory(
        user_id=1,
        title="Permanent Memory",
        content="This memory never expires",
        modality="text",
        created_at=datetime.utcnow() - timedelta(days=100),
        expiry_days=0  # 0 means never expire
    )
    session.add(permanent_memory)
    
    session.commit()

    # Store IDs for verification
    expired_id = expired_memory.id
    active_id = active_memory.id
    permanent_id = permanent_memory.id

    # Call delete_expired_memories
    memory_service.delete_expired_memories(session)

    # Refresh session
    session.expire_all()

    # Verify expired memory is deleted
    expired = session.query(Memory).filter(Memory.id == expired_id).first()
    assert expired is None, "Expired memory should be deleted"

    # Verify active memory still exists
    active = session.query(Memory).filter(Memory.id == active_id).first()
    assert active is not None, "Active memory should remain"
    assert active.title == "Active Memory"

    # Verify permanent memory still exists
    permanent = session.query(Memory).filter(Memory.id == permanent_id).first()
    assert permanent is not None, "Permanent memory should remain"
    assert permanent.title == "Permanent Memory"

def test_delete_expired_memories_with_no_expired(session):
    """Test delete_expired_memories when no memories are expired."""
    memory_service = MemoryService(db=None, vector_service=None, graph_service=None) # Mock db later if needed

    # Create only active memories
    active_memory = Memory(
        user_id=1,
        title="Active Memory",
        content="This memory is active",
        modality="text",
        created_at=datetime.utcnow(),
        expiry_days=30
    )
    session.add(active_memory)
    session.commit()

    active_id = active_memory.id

    # Call delete_expired_memories
    memory_service.delete_expired_memories(session)

    # Verify memory still exists
    active = session.query(Memory).filter(Memory.id == active_id).first()
    assert active is not None
    assert active.title == "Active Memory"

def test_memory_service_init():
    """Test MemoryService initialization."""
    service = MemoryService(db=None, vector_service=None, graph_service=None) # Mock db later if needed
    assert service is not None
    assert hasattr(service, 'vector_service')
    assert hasattr(service, 'graph_service')
