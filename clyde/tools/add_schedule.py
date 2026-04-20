from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.scheduler import SCHEDULER, ScheduledEvent


class AddScheduleResult(BaseModel):
    ok: bool
    schedule: ScheduledEvent | None = None
    error: str | None = None


@MCP.tool(description="Persist a new scheduled event. time is local 24h HH:MM. Event fires once per day at that time in the given room.")
async def add_schedule(event: str, room: str, time: str) -> AddScheduleResult:
    try:
        sched = ScheduledEvent(event=event, room=room, time=time)
    except ValueError as e:
        return AddScheduleResult(ok=False, error=str(e))
    added, error = await SCHEDULER.add(sched)
    if error:
        return AddScheduleResult(ok=False, error=str(error))
    return AddScheduleResult(ok=True, schedule=added)
