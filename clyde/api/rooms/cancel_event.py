from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.cancel_event import cancel_event

import clyde.utils as utils


class CancelEventRequest(BaseModel):
    room: str


class CancelEventResponse(BaseModel):
    room: str
    cancelled: bool


async def handle_cancel_event(req: CancelEventRequest) -> utils.Result[CancelEventResponse]:
    result = await cancel_event(room=req.room)
    if not result.ok:
        return utils.err(ValueError(result.error or "failed to cancel event"))
    return utils.ok(CancelEventResponse(room=req.room, cancelled=result.cancelled))


@MCP.custom_route("/api/rooms/{room}/event", methods=["DELETE"])
async def cancel_event_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, CancelEventRequest, handle_cancel_event)
