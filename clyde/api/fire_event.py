from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.fire_event import fire_event

import clyde.utils as utils


class FireEventRequest(BaseModel):
    room: str
    event: str


class FireEventResponse(BaseModel):
    room: str
    event: str


async def handle_fire_event(req: FireEventRequest) -> utils.Result[FireEventResponse]:
    result = await fire_event(room=req.room, event=req.event)
    if not result.ok:
        return utils.err(ValueError(result.error or "failed to fire event"))
    return utils.ok(FireEventResponse(room=req.room, event=req.event))


@MCP.custom_route("/api/rooms/{room}/event", methods=["POST"])
async def fire_event_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, FireEventRequest, handle_fire_event)
