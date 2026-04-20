from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.room_off import room_off

import clyde.utils as utils


class RoomOffRequest(BaseModel):
    room: str


class RoomOffResponse(BaseModel):
    room: str
    failed: dict[str, str]


async def handle_room_off(req: RoomOffRequest) -> utils.Result[RoomOffResponse]:
    result = await room_off(room=req.room)
    if not result.ok:
        return utils.err(ValueError(result.error or "failed to turn off room lights"))
    return utils.ok(RoomOffResponse(room=req.room, failed=result.failed))


@MCP.custom_route("/api/rooms/{room}/lights", methods=["DELETE"])
async def room_off_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, RoomOffRequest, handle_room_off)
