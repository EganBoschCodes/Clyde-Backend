from home_assistant_lib import LightOnPayload
from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.managers import ENGINE


class LightOnResult(BaseModel):
    ok: bool
    light: str
    error: str | None = None


@MCP.tool(description="Turn a single light on with optional RGB color (0-255 per channel), brightness (0-255), and transition seconds. Implicitly stops any routine active in that light's room.")
async def light_on(
    light: str,
    rgb: tuple[int, int, int] | None = None,
    brightness: int | None = None,
    transition: float | None = None,
) -> LightOnResult:
    room_key, error = ENGINE.find_room(light)
    if error:
        return LightOnResult(ok=False, light=light, error=str(error))
    manager, error = ENGINE.get(room_key)
    if error:
        return LightOnResult(ok=False, light=light, error=str(error))
    payload = LightOnPayload(rgb_color=rgb, brightness=brightness, transition=transition)
    _, error = await manager.apply_on(light, payload)
    if error:
        return LightOnResult(ok=False, light=light, error=str(error))
    return LightOnResult(ok=True, light=light)
