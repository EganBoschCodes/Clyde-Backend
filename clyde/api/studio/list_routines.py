from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.list_custom_routines import CustomRoutineInfo, list_custom_routines

import clyde.utils as utils


class ListStudioRoutinesRequest(BaseModel):
    pass


class ListStudioRoutinesResponse(BaseModel):
    routines: list[CustomRoutineInfo]


async def handle_list_studio_routines(req: ListStudioRoutinesRequest) -> utils.Result[ListStudioRoutinesResponse]:
    del req
    result = await list_custom_routines()
    return utils.ok(ListStudioRoutinesResponse(routines=result.routines))


@MCP.custom_route("/api/studio/routines", methods=["GET"])
async def list_routines_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, ListStudioRoutinesRequest, handle_list_studio_routines)
