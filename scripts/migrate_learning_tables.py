#!/usr/bin/env python3
"""
Migration script for learning tables.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.db.session import engine, Base
from app.models.learning.behaviour_event import BehaviourEvent
from app.models.learning.decision_trajectory import DecisionTrajectory
from app.models.learning.policy import Policy
from app.models.learning.behaviour_pack import BehaviourPack

async def migrate():
    print("🔧 Creating learning tables...")
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Learning tables created successfully")

if __name__ == "__main__":
    asyncio.run(migrate())
