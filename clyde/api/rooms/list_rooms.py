from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.list_rooms import RoomStatus, list_rooms

import clyde.utils as utils


class ListRoomsRequest(BaseModel):
    pass


class ListRoomsResponse(BaseModel):
    rooms: list[RoomStatus]


async def handle_list_rooms(req: ListRoomsRequest) -> utils.Result[ListRoomsResponse]:
    del req
    result = await list_rooms()
    return utils.ok(ListRoomsResponse(rooms=result.rooms))


@MCP.custom_route("/api/rooms", methods=["GET"])
async def list_rooms_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, ListRoomsRequest, handle_list_rooms)
