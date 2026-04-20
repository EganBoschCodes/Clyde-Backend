from pydantic import BaseModel

from clyde.events import EVENTS
from clyde.mcp_app import MCP
from clyde.routines import ENGINE


class FireEventResult(BaseModel):
    ok: bool
    room: str
    event: str | None = None
    error: str | None = None


@MCP.tool(description="Fire a transient light event in a room. The active routine (if any) is preempted and restored when the event completes. Use list_events to see available events.")
async def fire_event(room: str, event: str) -> FireEventResult:
    klass = EVENTS.get(event)
    if klass is None:
        return FireEventResult(ok=False, room=room, error=f"Unknown event '{event}'")
    _, error = await ENGINE.fire_event(room, klass())
    if error:
        return FireEventResult(ok=False, room=room, error=str(error))
    return FireEventResult(ok=True, room=room, event=event)
