from typing import Annotated

from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.state import Pin
from clyde.tools.light_off import light_off
from clyde.tools.light_on import light_on

import clyde.utils as utils


DEFAULT_OFF_TRANSITION_S = 1.0


class SetLightRequest(BaseModel):
    light: str
    on: bool
    rgb_color: tuple[Annotated[int, Field(ge=0, le=255)], Annotated[int, Field(ge=0, le=255)], Annotated[int, Field(ge=0, le=255)]] | None = None
    brightness: Annotated[int, Field(ge=1, le=255)] | None = None
    transition: Annotated[float, Field(ge=0.0)] | None = None


class SetLightResponse(BaseModel):
    light: str
    room: str
    pin: Pin


async def handle_set_light(req: SetLightRequest) -> utils.Result[SetLightResponse]:
    if not req.on:
        off_result = await light_off(light=req.light, transition=DEFAULT_OFF_TRANSITION_S if req.transition is None else req.transition)
        if not off_result.ok or off_result.pin is None or off_result.room is None:
            return utils.err(ValueError(off_result.error or "failed to turn off light"))
        return utils.ok(SetLightResponse(light=req.light, room=off_result.room, pin=off_result.pin))
    on_result = await light_on(light=req.light, rgb=req.rgb_color, brightness=req.brightness, transition=req.transition)
    if not on_result.ok or on_result.pin is None or on_result.room is None:
        return utils.err(ValueError(on_result.error or "failed to turn on light"))
    return utils.ok(SetLightResponse(light=req.light, room=on_result.room, pin=on_result.pin))


@MCP.custom_route("/api/lights/{light}", methods=["PUT"])
async def set_light_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, SetLightRequest, handle_set_light)
