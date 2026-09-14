import asyncio
from datetime import datetime
from app.services.blackboard import CognitiveBlackboard

async def test():
    bb = CognitiveBlackboard()
    await bb.post_insight(
        agent_name="TestAgent",
        insight={"event": "TestAction", "to": "TargetAgent", "data": {"key": "value"}},
        importance=0.8
    )
    print(bb.history)

asyncio.run(test())
