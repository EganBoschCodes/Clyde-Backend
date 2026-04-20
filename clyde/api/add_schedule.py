from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.scheduler import ScheduledEvent
from clyde.tools.add_schedule import add_schedule

import clyde.utils as utils


class AddScheduleRequest(BaseModel):
    event: str
    room: str
    time: str


class AddScheduleResponse(BaseModel):
    schedule: ScheduledEvent


async def handle_add_schedule(req: AddScheduleRequest) -> utils.Result[AddScheduleResponse]:
    result = await add_schedule(event=req.event, room=req.room, time=req.time)
    if not result.ok or result.schedule is None:
        return utils.err(ValueError(result.error or "failed to add schedule"))
    return utils.ok(AddScheduleResponse(schedule=result.schedule))


@MCP.custom_route("/api/schedules", methods=["POST"])
async def add_schedule_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, AddScheduleRequest, handle_add_schedule)
