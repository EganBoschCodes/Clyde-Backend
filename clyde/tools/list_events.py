from pydantic import BaseModel

from clyde.events import EVENTS
from clyde.mcp_app import MCP


class EventInfo(BaseModel):
    name: str


class ListEventsResult(BaseModel):
    events: list[EventInfo]


@MCP.tool(description="List all available light events (transient behaviors that preempt and restore the active routine).")
async def list_events() -> ListEventsResult:
    out = [EventInfo(name=name) for name in EVENTS.keys()]
    return ListEventsResult(events=out)
