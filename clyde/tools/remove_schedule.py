from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.scheduler import ScheduledEvent
from clyde.scheduler.scheduler import SCHEDULER


class RemoveScheduleResult(BaseModel):
    ok: bool
    schedule: ScheduledEvent | None = None
    error: str | None = None


@MCP.tool(description="Remove a persisted scheduled event by its (event, room, time) triple. time is local 24h HH:MM.")
async def remove_schedule(event: str, room: str, time: str) -> RemoveScheduleResult:
    removed, error = await SCHEDULER.remove((event, room, time))
    if error:
        return RemoveScheduleResult(ok=False, error=str(error))
    return RemoveScheduleResult(ok=True, schedule=removed)
