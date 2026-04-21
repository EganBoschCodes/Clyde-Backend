from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.scheduler import ScheduledEvent
from clyde.tools.remove_schedule import remove_schedule

import clyde.utils as utils


class RemoveScheduleRequest(BaseModel):
    event: str
    room: str
    time: str


class RemoveScheduleResponse(BaseModel):
    schedule: ScheduledEvent


async def handle_remove_schedule(req: RemoveScheduleRequest) -> utils.Result[RemoveScheduleResponse]:
    result = await remove_schedule(event=req.event, room=req.room, time=req.time)
    if not result.ok or result.schedule is None:
        return utils.err(ValueError(result.error or "failed to remove schedule"))
    return utils.ok(RemoveScheduleResponse(schedule=result.schedule))


@MCP.custom_route("/api/schedules", methods=["DELETE"])
async def remove_schedule_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, RemoveScheduleRequest, handle_remove_schedule)
