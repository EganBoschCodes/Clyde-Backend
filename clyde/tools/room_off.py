from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.managers import ENGINE


class RoomOffResult(BaseModel):
    ok: bool
    room: str
    failed: dict[str, str] = {}
    error: str | None = None


@MCP.tool(description="Turn every light in a room off with an optional transition (seconds). Implicitly stops any routine active in that room.")
async def room_off(room: str, transition: float = 1.0) -> RoomOffResult:
    manager, error = ENGINE.get(room)
    if error:
        return RoomOffResult(ok=False, room=room, error=str(error))
    failed, error = await manager.apply_off_all(transition=transition)
    if error:
        return RoomOffResult(ok=False, room=room, error=str(error))
    return RoomOffResult(ok=True, room=room, failed=failed)
