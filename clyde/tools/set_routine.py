from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.routines import ENGINE, ROUTINES


class SetRoutineResult(BaseModel):
    ok: bool
    room: str
    routine: str | None = None
    error: str | None = None


@MCP.tool(description="Start a light routine in a room. Any currently active routine in that room is stopped first. Use list_routines to see available routines.")
async def set_routine(room: str, routine: str) -> SetRoutineResult:
    klass = ROUTINES.get(routine)
    if klass is None:
        return SetRoutineResult(ok=False, room=room, error=f"Unknown routine '{routine}'")
    _, error = await ENGINE.start(room, klass())
    if error:
        return SetRoutineResult(ok=False, room=room, error=str(error))
    return SetRoutineResult(ok=True, room=room, routine=routine)
