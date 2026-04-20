from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.list_routines import list_routines


@MCP.custom_route("/api/routines", methods=["GET"])
async def list_routines_route(request: Request) -> JSONResponse:
    del request
    result = await list_routines()
    return JSONResponse(result.model_dump())
