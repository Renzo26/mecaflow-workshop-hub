import asyncio
import json
from typing import AsyncGenerator

from pydantic import BaseModel


class SSEBroadcaster:
    def __init__(self) -> None:
        self._queues: set[asyncio.Queue] = set()

    def _format(self, event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    async def publish(self, event: str, data: dict) -> None:
        payload = self._format(event, data)
        dead = set()
        for q in self._queues:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                dead.add(q)
        self._queues -= dead

    async def subscribe(self) -> AsyncGenerator[str, None]:
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._queues.add(queue)
        try:
            while True:
                payload = await queue.get()
                yield payload
        finally:
            self._queues.discard(queue)


broadcaster = SSEBroadcaster()
