from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.stop_routine import stop_routine

import clyde.utils as utils


class StopRoutineRequest(BaseModel):
    room: str


class StopRoutineResponse(BaseModel):
    room: str


async def handle_stop_routine(req: StopRoutineRequest) -> utils.Result[StopRoutineResponse]:
    result = await stop_routine(room=req.room)
    if not result.ok:
        return utils.err(ValueError(result.error or "failed to stop routine"))
    return utils.ok(StopRoutineResponse(room=req.room))


@MCP.custom_route("/api/rooms/{room}/routine", methods=["DELETE"])
async def stop_routine_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, StopRoutineRequest, handle_stop_routine)
