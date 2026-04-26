from pydantic import BaseModel

from home_assistant_lib import LightState

from clyde.mcp_app import MCP

import clyde.utils as utils


class LightStateResult(BaseModel):
    ok: bool
    light: str
    state: LightState | None = None
    error: str | None = None


@MCP.tool(description="Get the current state of a light: power, brightness (0-255), and rgb_color.")
async def light_state(light: str) -> LightStateResult:
    light_obj = utils.CONFIG.lights.get(light)
    if light_obj is None:
        return LightStateResult(ok=False, light=light, error=f"Unknown light '{light}'")
    state, error = light_obj.get_state()
    if error:
        return LightStateResult(ok=False, light=light, error=str(error))
    return LightStateResult(ok=True, light=light, state=state)
