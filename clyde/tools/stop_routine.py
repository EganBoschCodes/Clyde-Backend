from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.routines import ENGINE


class StopRoutineResult(BaseModel):
    ok: bool
    room: str
    error: str | None = None


@MCP.tool(description="Stop the active routine in a room. Lights remain in their last state (does not turn them off).")
async def stop_routine(room: str) -> StopRoutineResult:
    _, error = await ENGINE.stop(room)
    if error:
        return StopRoutineResult(ok=False, room=room, error=str(error))
    return StopRoutineResult(ok=True, room=room)
