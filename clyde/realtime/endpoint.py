import asyncio
import logging

from starlette.websockets import WebSocket, WebSocketDisconnect

from .bus import BUS


logger = logging.getLogger(__name__)


async def pump_outbound(ws: WebSocket, queue: asyncio.Queue[str]) -> None:
    while True:
        payload = await queue.get()
        await ws.send_text(payload)


async def pump_inbound(ws: WebSocket) -> None:
    while True:
        await ws.receive_text()


async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    queue = BUS.subscribe()
    outbound = asyncio.create_task(pump_outbound(ws, queue))
    inbound = asyncio.create_task(pump_inbound(ws))
    try:
        done, pending = await asyncio.wait({outbound, inbound}, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        for task in done:
            error = task.exception()
            if error and not isinstance(error, WebSocketDisconnect):
                logger.warning(f"[realtime] websocket task error: {error}")
    finally:
        BUS.unsubscribe(queue)
