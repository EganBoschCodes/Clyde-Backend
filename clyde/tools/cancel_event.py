from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.managers import ENGINE


class CancelEventResult(BaseModel):
    ok: bool
    room: str
    cancelled: bool = False
    error: str | None = None


@MCP.tool(description="Cancel the event currently running in a room (if any). The prior routine or light state is restored. Returns cancelled=false when no event was running.")
async def cancel_event(room: str) -> CancelEventResult:
    cancelled, error = await ENGINE.cancel_event(room)
    if error:
        return CancelEventResult(ok=False, room=room, error=str(error))
    return CancelEventResult(ok=True, room=room, cancelled=cancelled)
