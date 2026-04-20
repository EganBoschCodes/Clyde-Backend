from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.stop_routine import stop_routine


@MCP.custom_route("/api/rooms/{room}/routine", methods=["DELETE"])
async def stop_routine_route(request: Request) -> JSONResponse:
    room = request.path_params["room"]
    result = await stop_routine(room=room)
    status = 200 if result.ok else 400
    return JSONResponse(result.model_dump(), status_code=status)
