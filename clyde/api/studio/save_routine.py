from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.routines import CustomRoutineSpec
from clyde.tools.list_custom_routines import CustomRoutineInfo
from clyde.tools.save_custom_routine import save_custom_routine

import clyde.utils as utils


class SaveStudioRoutineRequest(CustomRoutineSpec):
    key: str | None = None


async def handle_save_studio_routine(req: SaveStudioRoutineRequest) -> utils.Result[CustomRoutineInfo]:
    result = await save_custom_routine(name=req.name, colors=req.colors, style=req.style, speed=req.speed, brightness=req.brightness, key=req.key)
    if not result.ok or result.routine is None:
        return utils.err(ValueError(result.error or "failed to save routine"))
    return utils.ok(result.routine)


@MCP.custom_route("/api/studio/routines", methods=["PUT"])
async def save_routine_route(request: Request) -> JSONResponse:
    return await utils.handle_api(request, SaveStudioRoutineRequest, handle_save_studio_routine)
