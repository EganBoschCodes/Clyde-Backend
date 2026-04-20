from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.scheduler import ScheduledEvent
from clyde.tools.list_schedules import list_schedules

import clyde.utils as utils


class ListSchedulesRequest(BaseModel):
    pass


class ListSchedulesResponse(BaseModel):
    schedules: list[ScheduledEvent]


async def handle_list_schedules(req: ListSchedulesRequest) -> utils.Result[ListSchedulesResponse]:
    del req
    result = await list_schedules()
    return utils.ok(ListSchedulesResponse(schedules=result.schedules))


@MCP.custom_route("/api/schedules", methods=["GET"])
async def list_schedules_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, ListSchedulesRequest, handle_list_schedules)
