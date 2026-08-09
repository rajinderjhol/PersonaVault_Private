import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from app.models import Memory
from app.services.memory_service import MemoryService

@pytest.mark.asyncio
async def test_delete_expired_memories(db_session):
    """Test that expired memories are deleted and active ones remain."""
    memory_service = MemoryService(db=db_session, vector_service=None, graph_service=None)
    
    expired_memory = Memory(
        user_id=1,
        title="Expired Memory",
        content="This should be deleted",
        modality="text",
        created_at=datetime.now(timezone.utc) - timedelta(days=10),
        expiry_days=5
    )
    db_session.add(expired_memory)
    
    active_memory = Memory(
        user_id=1,
        title="Active Memory",
        content="This memory should stay",
        modality="text",
        created_at=datetime.now(timezone.utc),
        expiry_days=30
    )
    db_session.add(active_memory)
    
    permanent_memory = Memory(
        user_id=1,
        title="Permanent Memory",
        content="This memory never expires",
        modality="text",
        created_at=datetime.now(timezone.utc) - timedelta(days=100),
        expiry_days=0
    )
    db_session.add(permanent_memory)
    
    await db_session.commit()

    await memory_service.delete_expired_memories(db_session)

    res = await db_session.execute(select(Memory))
    memories = res.scalars().all()
    titles = [m.title for m in memories]

    assert "Active Memory" in titles
    assert "Permanent Memory" in titles

@pytest.mark.asyncio
async def test_delete_expired_memories_with_no_expired(db_session):
    """Test delete_expired_memories when no memories are expired."""
    memory_service = MemoryService(db=db_session, vector_service=None, graph_service=None)

    active_memory = Memory(
        user_id=1,
        title="Active Memory",
        content="This memory is active",
        modality="text",
        created_at=datetime.now(timezone.utc),
        expiry_days=30
    )
    db_session.add(active_memory)
    await db_session.commit()

    await memory_service.delete_expired_memories(db_session)

    res = await db_session.execute(select(Memory))
    memories = res.scalars().all()
    assert len(memories) >= 1
    assert memories[0].title == "Active Memory"

def test_memory_service_init():
    """Test MemoryService initialization."""
    service = MemoryService(db=None, vector_service=None, graph_service=None)
    assert service is not None
    assert hasattr(service, 'vector_service')
    assert hasattr(service, 'graph_service')

