from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.managers import ENGINE


class ReleaseLightResult(BaseModel):
    ok: bool
    light: str
    room: str | None = None
    released: bool = False
    error: str | None = None


@MCP.tool(description="Release a pinned light. If a routine is active in the light's room it rejoins on the next tick; otherwise the light simply stays as it is. `released` is false if the light was not pinned.")
async def release_light(light: str) -> ReleaseLightResult:
    room_key, error = ENGINE.find_room(light)
    if error:
        return ReleaseLightResult(ok=False, light=light, error=str(error))
    manager, error = ENGINE.get(room_key)
    if error:
        return ReleaseLightResult(ok=False, light=light, room=room_key, error=str(error))
    released, error = await manager.release_pin(light)
    if error:
        return ReleaseLightResult(ok=False, light=light, room=room_key, error=str(error))
    return ReleaseLightResult(ok=True, light=light, room=room_key, released=released)
