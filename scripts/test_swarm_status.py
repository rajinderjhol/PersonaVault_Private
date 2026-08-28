#!/usr/bin/env python3
"""
Test swarm status visibility.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.swarm.orchestrator import MultiAgentOrchestrator


async def test_swarm_status():
    print("🐝 Testing Swarm Status")
    print("=" * 50)
    
    orchestrator = MultiAgentOrchestrator(db_session=None, blackboard=None)
    
    # Get swarm status
    status = await orchestrator.get_swarm_status()
    
    print("\n📊 Swarm Status:")
    print(f"   Total Agents: {status.get('total_agents', 0)}")
    print(f"   Active Agents: {status.get('active_count', 0)}")
    print(f"   Idle Agents: {len(status.get('idle_agents', []))}")
    
    print("\n🔄 Active Agents:")
    for agent in status.get('active_agents', []):
        print(f"   - {agent['name']}: {agent.get('task', 'Processing')}")
        print(f"     Provider: {agent.get('provider', 'unknown')}")
        print(f"     Confidence: {agent.get('confidence', 0.5):.2f}")
    
    print("\n💤 Idle Agents:")
    for agent in status.get('idle_agents', []):
        print(f"   - {agent}")
    
    print("\n🔗 Collaboration Pipeline:")
    pipeline = status.get('collaboration', {})
    print(f"   Pipeline: {' → '.join(pipeline.get('pipeline', []))}")
    print(f"   Current Step: {pipeline.get('current_step', 'None')}")
    print(f"   Active: {pipeline.get('active', False)}")
    
    print("\n✅ Swarm status test complete!")


if __name__ == "__main__":
    asyncio.run(test_swarm_status())
