from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.managers import ENGINE
from clyde.state import Pin


class LightOffResult(BaseModel):
    ok: bool
    light: str
    room: str | None = None
    pin: Pin | None = None
    error: str | None = None


@MCP.tool(description="Turn a single light off with an optional transition (seconds). The light is PINNED off: it leaves the room's routine and stays off while the routine keeps animating the other lights. Use release_light to let it rejoin the routine; starting a new routine or turning the room off clears all pins.")
async def light_off(light: str, transition: float = 1.0) -> LightOffResult:
    room_key, error = ENGINE.find_room(light)
    if error:
        return LightOffResult(ok=False, light=light, error=str(error))
    manager, error = ENGINE.get(room_key)
    if error:
        return LightOffResult(ok=False, light=light, room=room_key, error=str(error))
    pin, error = await manager.pin_light(light, on=False, transition=transition)
    if error:
        return LightOffResult(ok=False, light=light, room=room_key, error=str(error))
    return LightOffResult(ok=True, light=light, room=room_key, pin=pin)
