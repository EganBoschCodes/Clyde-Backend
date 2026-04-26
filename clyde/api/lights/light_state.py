from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from home_assistant_lib import LightState

from clyde.mcp_app import MCP
from clyde.tools.light_state import light_state

import clyde.utils as utils


class LightStateRequest(BaseModel):
    light: str


class LightStateResponse(BaseModel):
    light: str
    state: LightState


async def handle_light_state(req: LightStateRequest) -> utils.Result[LightStateResponse]:
    result = await light_state(light=req.light)
    if not result.ok or result.state is None:
        return utils.err(ValueError(result.error or "light state lookup failed"))
    return utils.ok(LightStateResponse(light=req.light, state=result.state))


@MCP.custom_route("/api/lights/{light}/state", methods=["GET"])
async def light_state_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, LightStateRequest, handle_light_state)
