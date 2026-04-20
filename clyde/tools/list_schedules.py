from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.scheduler import SCHEDULER, ScheduledEvent


class ListSchedulesResult(BaseModel):
    schedules: list[ScheduledEvent]


@MCP.tool(description="List all persisted scheduled events. Each runs once per day at its specified local time.")
async def list_schedules() -> ListSchedulesResult:
    return ListSchedulesResult(schedules=SCHEDULER.list())
