from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.managers import ENGINE


class SetDimResult(BaseModel):
    ok: bool
    room: str
    factor: float | None = None
    error: str | None = None


@MCP.tool(description="Set a room's universal dim factor (0.0 to 1.0). Scales the brightness of every light payload sent to that room, so routines and direct light_on commands both honor the slider. 1.0 = full brightness, 0.0 = fully dimmed.")
async def set_dim(room: str, factor: float) -> SetDimResult:
    applied, error = ENGINE.set_dim_factor(room, factor)
    if error:
        return SetDimResult(ok=False, room=room, error=str(error))
    return SetDimResult(ok=True, room=room, factor=applied)
