from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.delete_custom_routine import delete_custom_routine

import clyde.utils as utils


class DeleteStudioRoutineRequest(BaseModel):
    key: str


class DeleteStudioRoutineResponse(BaseModel):
    key: str


async def handle_delete_studio_routine(req: DeleteStudioRoutineRequest) -> utils.Result[DeleteStudioRoutineResponse]:
    result = await delete_custom_routine(key=req.key)
    if not result.ok:
        return utils.err(ValueError(result.error or "failed to delete routine"))
    return utils.ok(DeleteStudioRoutineResponse(key=req.key))


@MCP.custom_route("/api/studio/routines/{key}", methods=["DELETE"])
async def delete_routine_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, DeleteStudioRoutineRequest, handle_delete_studio_routine)
