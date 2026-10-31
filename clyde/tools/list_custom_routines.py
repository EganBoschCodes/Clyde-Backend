from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.routines.custom import CustomRoutineSpec
from clyde.state import STATE


class CustomRoutineInfo(CustomRoutineSpec):
    key: str


class ListCustomRoutinesResult(BaseModel):
    routines: list[CustomRoutineInfo]


@MCP.tool(description="List user-made custom light routines (Studio) with their key, name, colors, style, speed (0 chill to 1 fast) and brightness. Use the key with set_routine to start one.")
async def list_custom_routines() -> ListCustomRoutinesResult:
    out = [CustomRoutineInfo(key=key, **spec.model_dump()) for key, spec in STATE.custom_routines().items()]
    return ListCustomRoutinesResult(routines=out)
