import pytest
from app.models import Memory, SemanticPattern
from app.services.memory_service import MemoryService

@pytest.mark.asyncio
async def test_memory_graduation_integrity(db_session, app_state):
    """Verifies that the Leapfrog strategy correctly graduates L2 memories to L3."""
    memory_service = MemoryService(db=lambda: db_session, vector_service=None, graph_service=None)
    
    # 1. Create a cluster of similar episodic memories (Layer 2)
    for i in range(5):
        mem = Memory(
            content=f"User prefers dark mode UI for the {i}th time",
            category="preference",
            metadata_json={"source": "test"}
        )
        db_session.add(mem)
    await db_session.commit()

    # 2. Manually trigger a graduation check
    # (This mirrors what the ConsolidationTask does in the background)
    task = app_state.consolidation_task
    await task.process_layer2_batch()
    
    # 3. Assert that a Semantic Pattern (Layer 3) was created
    # Use select() to check for the graduation result
    from sqlalchemy import select
    result = await db_session.execute(select(SemanticPattern))
    patterns = result.scalars().all()
    
    assert len(patterns) > 0
    assert "dark mode" in patterns[0].pattern_statement.lower()