#!/usr/bin/env python3
"""
Migration script for conflict resolution tables.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.db.session import engine, Base
from app.models.learning.vector_clock import VectorClock
from app.services.idempotency import IdempotentAction

async def migrate():
    print("🔧 Creating conflict resolution tables...")
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created successfully")

if __name__ == "__main__":
    asyncio.run(migrate())
