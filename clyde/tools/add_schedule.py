from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.scheduler import ScheduledEvent
from clyde.scheduler.scheduler import SCHEDULER


class AddScheduleResult(BaseModel):
    ok: bool
    schedule: ScheduledEvent | None = None
    error: str | None = None


@MCP.tool(description="Persist a new scheduled event. time is local 24h HH:MM. days_of_week is a list of weekdays the schedule fires on, where 0=Mon and 6=Sun (must include at least one day).")
async def add_schedule(event: str, room: str, time: str, days_of_week: list[int]) -> AddScheduleResult:
    try:
        sched = ScheduledEvent(event=event, room=room, time=time, days_of_week=tuple(days_of_week))
    except ValueError as e:
        return AddScheduleResult(ok=False, error=str(e))
    added, error = await SCHEDULER.add(sched)
    if error:
        return AddScheduleResult(ok=False, error=str(error))
    return AddScheduleResult(ok=True, schedule=added)
