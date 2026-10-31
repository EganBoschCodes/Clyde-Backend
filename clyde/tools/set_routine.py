from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.managers import ENGINE
from clyde.routines.resolve import resolve_routine


class SetRoutineResult(BaseModel):
    ok: bool
    room: str
    routine: str | None = None
    error: str | None = None


@MCP.tool(description="Start a light routine in a room. Any currently active routine in that room is stopped first. Use list_routines to see available routines.")
async def set_routine(room: str, routine: str) -> SetRoutineResult:
    instance, error = resolve_routine(routine)
    if error:
        return SetRoutineResult(ok=False, room=room, error=str(error))
    _, error = await ENGINE.start(room, instance)
    if error:
        return SetRoutineResult(ok=False, room=room, error=str(error))
    return SetRoutineResult(ok=True, room=room, routine=routine)
