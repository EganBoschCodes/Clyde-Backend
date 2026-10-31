from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.routines import ROUTINES, build_custom_routine
from clyde.state import STATE


class RoutineInfo(BaseModel):
    name: str
    tick_interval: float
    custom: bool
    display_name: str


class ListRoutinesResult(BaseModel):
    routines: list[RoutineInfo]


@MCP.tool(description="List all available light routines (built-in and user-made custom ones) with their tick interval in seconds. Custom routines have custom=true and a human-readable display_name.")
async def list_routines() -> ListRoutinesResult:
    out = [RoutineInfo(name=name, tick_interval=klass.tick_interval, custom=False, display_name=name) for name, klass in ROUTINES.items()]
    for key, spec in STATE.custom_routines().items():
        routine = build_custom_routine(key, spec)
        out.append(RoutineInfo(name=key, tick_interval=routine.tick_interval, custom=True, display_name=spec.name))
    return ListRoutinesResult(routines=out)
