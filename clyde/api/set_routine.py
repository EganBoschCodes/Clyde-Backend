from starlette.requests import Request
from starlette.responses import JSONResponse

from clyde.mcp_app import MCP
from clyde.tools.set_routine import set_routine


@MCP.custom_route("/api/rooms/{room}/routine", methods=["POST"])
async def set_routine_route(request: Request) -> JSONResponse:
    room = request.path_params["room"]
    body = await request.json()
    routine = body.get("routine")
    if not isinstance(routine, str):
        return JSONResponse({"ok": False, "error": "body must contain 'routine' (string)"}, status_code=400)
    result = await set_routine(room=room, routine=routine)
    status = 200 if result.ok else 400
    return JSONResponse(result.model_dump(), status_code=status)
