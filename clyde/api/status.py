from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP

import clyde.utils as utils


class StatusRequest(BaseModel):
    pass


class StatusResponse(BaseModel):
    status: str
    service: str


async def handle_status(req: StatusRequest) -> utils.Result[StatusResponse]:
    del req
    return utils.ok(StatusResponse(status="ready", service="clyde"))


@MCP.custom_route("/api/status", methods=["GET"])
async def status_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, StatusRequest, handle_status)
