from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.list_rooms import list_rooms


@MCP.custom_route("/api/rooms", methods=["GET"])
async def list_rooms_route(request: Request) -> JSONResponse:
    del request
    result = await list_rooms()
    return JSONResponse(result.model_dump())
