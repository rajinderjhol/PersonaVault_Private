import asyncio
from app.services.blackboard import CognitiveBlackboard

async def test():
    bb = CognitiveBlackboard()
    await bb.post_insight("Agent", {"event": "test"}, "Target", 0.5)
    print(f"History length: {len(bb.history)}")
    print(f"History: {bb.history}")

asyncio.run(test())
