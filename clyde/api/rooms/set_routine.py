from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.set_routine import set_routine

import clyde.utils as utils


class SetRoutineRequest(BaseModel):
    room: str
    routine: str


class SetRoutineResponse(BaseModel):
    room: str
    routine: str


async def handle_set_routine(req: SetRoutineRequest) -> utils.Result[SetRoutineResponse]:
    result = await set_routine(room=req.room, routine=req.routine)
    if not result.ok:
        return utils.err(ValueError(result.error or "failed to set routine"))
    return utils.ok(SetRoutineResponse(room=req.room, routine=req.routine))


@MCP.custom_route("/api/rooms/{room}/routine", methods=["POST"])
async def set_routine_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, SetRoutineRequest, handle_set_routine)
