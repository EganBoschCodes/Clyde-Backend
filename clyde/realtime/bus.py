import asyncio
import logging

from .messages import RealtimeEvent


logger = logging.getLogger(__name__)

QUEUE_MAXSIZE = 64


class RealtimeBus:
    def __init__(self) -> None:
        self.subscribers: set[asyncio.Queue[str]] = set()

    def subscribe(self) -> asyncio.Queue[str]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=QUEUE_MAXSIZE)
        self.subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[str]) -> None:
        self.subscribers.discard(queue)

    def publish(self, event: RealtimeEvent) -> None:
        if not self.subscribers:
            return
        payload = event.model_dump_json()
        for queue in list(self.subscribers):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                logger.warning("[realtime] dropping slow subscriber")
                self.subscribers.discard(queue)


BUS = RealtimeBus()
