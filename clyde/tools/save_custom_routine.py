from pydantic import BaseModel

import clyde.utils as utils

from clyde.managers import ENGINE
from clyde.mcp_app import MCP
from clyde.routines import ROUTINES, CustomRoutineSpec, build_custom_routine
from clyde.routines.custom import slugify, validate_key
from clyde.state import STATE

from .list_custom_routines import CustomRoutineInfo


class SaveCustomRoutineResult(BaseModel):
    ok: bool
    routine: CustomRoutineInfo | None = None
    error: str | None = None


def resolve_key(name: str, key: str | None) -> utils.Result[str]:
    resolved, error = validate_key(key) if key is not None else slugify(name)
    if error:
        return utils.err(error)
    if resolved in ROUTINES:
        return utils.err(ValueError(f"Routine key '{resolved}' collides with a built-in routine"))
    return utils.ok(resolved)


@MCP.tool(description="Create or update a custom light routine. style is one of drift, flicker, pulse, chase, static. colors is 1-8 hex strings like #FF8800. speed is 0 (slowest) to 1 (fastest). brightness is 1-255. The key is derived from the name (studio_<slug>) unless an existing key is passed to edit it; saving a routine that is running restarts it with the new settings.")
async def save_custom_routine(name: str, colors: list[str], style: str, speed: float, brightness: int, key: str | None = None) -> SaveCustomRoutineResult:
    spec, error = utils.safe_validate(CustomRoutineSpec, {"name": name, "colors": colors, "style": style, "speed": speed, "brightness": brightness})
    if error:
        return SaveCustomRoutineResult(ok=False, error=str(error))
    resolved, error = resolve_key(spec.name, key)
    if error:
        return SaveCustomRoutineResult(ok=False, error=str(error))
    _, error = STATE.set_custom_routine(resolved, spec)
    if error:
        return SaveCustomRoutineResult(ok=False, error=str(error))
    for room in ENGINE.rooms_running(resolved):
        _, error = await ENGINE.start(room, build_custom_routine(resolved, spec))
        if error:
            print(f"[studio] restart '{resolved}' in '{room}' failed: {error}")
    return SaveCustomRoutineResult(ok=True, routine=CustomRoutineInfo(key=resolved, **spec.model_dump()))
