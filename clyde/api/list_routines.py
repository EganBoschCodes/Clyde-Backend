from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.list_routines import RoutineInfo, list_routines

import clyde.utils as utils


class ListRoutinesRequest(BaseModel):
    pass


class ListRoutinesResponse(BaseModel):
    routines: list[RoutineInfo]


async def handle_list_routines(req: ListRoutinesRequest) -> utils.Result[ListRoutinesResponse]:
    del req
    result = await list_routines()
    return utils.ok(ListRoutinesResponse(routines=result.routines))


@MCP.custom_route("/api/routines", methods=["GET"])
async def list_routines_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, ListRoutinesRequest, handle_list_routines)
