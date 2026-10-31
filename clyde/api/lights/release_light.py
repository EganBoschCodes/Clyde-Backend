from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.release_light import release_light

import clyde.utils as utils


class ReleaseLightRequest(BaseModel):
    light: str


class ReleaseLightResponse(BaseModel):
    light: str
    room: str
    released: bool


async def handle_release_light(req: ReleaseLightRequest) -> utils.Result[ReleaseLightResponse]:
    result = await release_light(light=req.light)
    if not result.ok or result.room is None:
        return utils.err(ValueError(result.error or "failed to release light"))
    return utils.ok(ReleaseLightResponse(light=req.light, room=result.room, released=result.released))


@MCP.custom_route("/api/lights/{light}/pin", methods=["DELETE"])
async def release_light_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, ReleaseLightRequest, handle_release_light)
