from home_assistant_lib import LightOnPayload
from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.managers import ENGINE
from clyde.state import Pin


class LightOnResult(BaseModel):
    ok: bool
    light: str
    room: str | None = None
    pin: Pin | None = None
    error: str | None = None


@MCP.tool(description="Turn a single light on with optional RGB color (0-255 per channel), brightness (1-255), and transition seconds. The light is PINNED: it leaves the room's routine and holds this state while the routine keeps animating the other lights. Omitted color/brightness keep the light's current values. Use release_light to let it rejoin the routine; starting a new routine or turning the room off clears all pins.")
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
        return LightOnResult(ok=False, light=light, room=room_key, error=str(error))
    pin, error = await manager.pin_light(light, on=True, rgb_color=rgb, brightness=brightness, transition=transition)
    if error:
        return LightOnResult(ok=False, light=light, room=room_key, error=str(error))
    return LightOnResult(ok=True, light=light, room=room_key, pin=pin)
