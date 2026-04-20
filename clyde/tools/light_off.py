from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.routines import ENGINE


class LightOffResult(BaseModel):
    ok: bool
    light: str
    error: str | None = None


@MCP.tool(description="Turn a single light off with an optional transition (seconds). Implicitly stops any routine active in that light's room.")
async def light_off(light: str, transition: float = 1.0) -> LightOffResult:
    room_key, error = ENGINE.find_room(light)
    if error:
        return LightOffResult(ok=False, light=light, error=str(error))
    manager, error = ENGINE.get(room_key)
    if error:
        return LightOffResult(ok=False, light=light, error=str(error))
    _, error = await manager.apply_off(light, transition=transition)
    if error:
        return LightOffResult(ok=False, light=light, error=str(error))
    return LightOffResult(ok=True, light=light)
