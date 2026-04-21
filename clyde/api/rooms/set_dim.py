from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.set_dim import set_dim

import clyde.utils as utils


class SetDimRequest(BaseModel):
    room: str
    factor: float


class SetDimResponse(BaseModel):
    room: str
    factor: float


async def handle_set_dim(req: SetDimRequest) -> utils.Result[SetDimResponse]:
    result = await set_dim(room=req.room, factor=req.factor)
    if not result.ok or result.factor is None:
        return utils.err(ValueError(result.error or "failed to set dim factor"))
    return utils.ok(SetDimResponse(room=req.room, factor=result.factor))


@MCP.custom_route("/api/rooms/{room}/dim", methods=["PUT"])
async def set_dim_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, SetDimRequest, handle_set_dim)
