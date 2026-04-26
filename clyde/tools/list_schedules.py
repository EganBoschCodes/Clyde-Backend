from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.scheduler import ScheduledEvent
from clyde.scheduler.scheduler import SCHEDULER


class ListSchedulesResult(BaseModel):
    schedules: list[ScheduledEvent]


@MCP.tool(description="List all persisted scheduled events. Each fires at its specified local time on the weekdays listed in days_of_week (0=Mon, 6=Sun).")
async def list_schedules() -> ListSchedulesResult:
    return ListSchedulesResult(schedules=SCHEDULER.list())
