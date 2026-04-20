from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.list_lights import LightInfo, list_lights

import clyde.utils as utils


class ListLightsRequest(BaseModel):
    room: str | None = None


class ListLightsResponse(BaseModel):
    lights: list[LightInfo]


async def handle_list_lights(req: ListLightsRequest) -> utils.Result[ListLightsResponse]:
    result = await list_lights(room=req.room)
    return utils.ok(ListLightsResponse(lights=result.lights))


@MCP.custom_route("/api/lights", methods=["GET"])
async def list_lights_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, ListLightsRequest, handle_list_lights)
