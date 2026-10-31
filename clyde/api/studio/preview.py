from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.managers import ENGINE
from clyde.mcp_app import MCP
from clyde.routines import CustomRoutineSpec, build_custom_routine
from clyde.routines.custom import PREVIEW_KEY

import clyde.utils as utils


class PreviewRequest(BaseModel):
    room: str
    spec: CustomRoutineSpec


class PreviewResponse(BaseModel):
    room: str
    routine: str


async def handle_preview(req: PreviewRequest) -> utils.Result[PreviewResponse]:
    _, error = await ENGINE.start(req.room, build_custom_routine(PREVIEW_KEY, req.spec))
    if error:
        return utils.err(error, f"preview in '{req.room}'")
    return utils.ok(PreviewResponse(room=req.room, routine=PREVIEW_KEY))


@MCP.custom_route("/api/studio/preview", methods=["POST"])
async def preview_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, PreviewRequest, handle_preview)
