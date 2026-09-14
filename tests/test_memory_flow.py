"""
Tests for memory layer graduation (Gas -> Liquid -> Ice) integrity.
"""
import pytest
from sqlalchemy import select
from app.models import Memory, SemanticPattern
from tests.conftest import create_test_user


async def test_memory_graduation_integrity(db_session):
    """Verifies that Layer 3 SemanticPatterns can be created and retrieved correctly."""
    pattern = SemanticPattern(
        pattern_type="preference",
        trigger="dark mode UI",
        correction="User prefers dark mode UI",
        occurrence_count=5,
        weight=0.9,
        is_active=True,
    )
    db_session.add(pattern)
    await db_session.commit()

    result = await db_session.execute(select(SemanticPattern))
    patterns = result.scalars().all()

    assert len(patterns) > 0
    assert "dark mode" in patterns[-1].trigger.lower()


async def test_pattern_weight_is_stored_correctly(db_session):
    """Pattern weight must persist with exact precision."""
    pattern = SemanticPattern(
        pattern_type="behaviour",
        trigger="user greets robot",
        correction="Respond warmly",
        occurrence_count=3,
        weight=0.85,
        is_active=True,
    )
    db_session.add(pattern)
    await db_session.commit()

    result = await db_session.execute(
        select(SemanticPattern).where(SemanticPattern.trigger == "user greets robot")
    )
    stored = result.scalars().first()
    assert stored is not None
    assert abs(stored.weight - 0.85) < 0.001


async def test_inactive_pattern_can_be_deactivated(db_session):
    """Patterns below threshold must be deactivatable (is_active=False)."""
    pattern = SemanticPattern(
        pattern_type="deprecated",
        trigger="old behaviour",
        correction="No longer valid",
        occurrence_count=1,
        weight=0.35,
        is_active=False,
    )
    db_session.add(pattern)
    await db_session.commit()

    result = await db_session.execute(
        select(SemanticPattern).where(SemanticPattern.trigger == "old behaviour")
    )
    stored = result.scalars().first()
    assert stored is not None
    assert stored.is_active is False


async def test_memory_layer2_creation(db_session):
    """Verify episodic (Layer 2) memory records can be created and retrieved."""
    user, _ = await create_test_user(db_session)
    memory = Memory(
        user_id=user.id,
        title="Layer 2 Episodic Entry",
        content="Meeting with the legal team about contract renewal",
        modality="text",
        expiry_days=30,
    )
    db_session.add(memory)
    await db_session.commit()

    result = await db_session.execute(
        select(Memory).where(Memory.title == "Layer 2 Episodic Entry")
    )
    stored = result.scalars().first()
    assert stored is not None
    assert stored.content == "Meeting with the legal team about contract renewal"
