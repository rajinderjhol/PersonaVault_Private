"""
Response streaming utilities for better UX and memory efficiency.
"""
import asyncio
from typing import AsyncGenerator

async def stream_response(generator: AsyncGenerator) -> AsyncGenerator[str, None]:
    """Stream a response token by token."""
    async for chunk in generator:
        yield f"data: {chunk}\n\n"
        await asyncio.sleep(0.01)  # Yield control to event loop
