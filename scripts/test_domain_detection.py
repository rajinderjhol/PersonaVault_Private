import asyncio
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.swarm.routing.domain_detector import DomainDetector
from app.swarm.routing.domain_router import DomainRouter

async def main():
    detector = DomainDetector()
    router = DomainRouter()
    print("Testing Detection...")
    res = await detector.detect("patient has chest pain")
    print(f"Result: {res.domain}")
    print("Testing Routing...")
    res = await router.route("patient has chest pain")
    print(f"Route: {res.domain}")

if __name__ == "__main__":
    asyncio.run(main())
