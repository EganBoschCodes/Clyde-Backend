from pydantic import BaseModel

from clyde.managers import ENGINE
from clyde.mcp_app import MCP
from clyde.state import STATE


class DeleteCustomRoutineResult(BaseModel):
    ok: bool
    key: str
    error: str | None = None


@MCP.tool(description="Delete a custom light routine by key. It is stopped in any room where it is currently running.")
async def delete_custom_routine(key: str) -> DeleteCustomRoutineResult:
    _, error = STATE.delete_custom_routine(key)
    if error:
        return DeleteCustomRoutineResult(ok=False, key=key, error=str(error))
    for room in ENGINE.rooms_running(key):
        _, error = await ENGINE.stop(room)
        if error:
            print(f"[studio] stop '{key}' in '{room}' failed: {error}")
    return DeleteCustomRoutineResult(ok=True, key=key)
