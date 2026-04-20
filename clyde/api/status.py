from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP


@MCP.custom_route("/api/status", methods=["GET"])
async def status(request: Request) -> JSONResponse:
    del request
    return JSONResponse({"status": "ready", "service": "clyde"})
