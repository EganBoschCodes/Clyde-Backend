from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.routines import ROUTINES


class RoutineInfo(BaseModel):
    name: str
    tick_interval: float


class ListRoutinesResult(BaseModel):
    routines: list[RoutineInfo]


@MCP.tool(description="List all available light routines with their tick interval in seconds.")
async def list_routines() -> ListRoutinesResult:
    out = [RoutineInfo(name=name, tick_interval=klass.tick_interval) for name, klass in ROUTINES.items()]
    return ListRoutinesResult(routines=out)
