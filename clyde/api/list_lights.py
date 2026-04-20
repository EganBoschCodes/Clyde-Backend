from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.list_lights import list_lights


@MCP.custom_route("/api/lights", methods=["GET"])
async def list_lights_route(request: Request) -> JSONResponse:
    room = request.query_params.get("room")
    result = await list_lights(room=room)
    return JSONResponse(result.model_dump())
