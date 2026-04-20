from pydantic import BaseModel

from clyde.mcp_app import MCP

import clyde.utils as utils


class LightInfo(BaseModel):
    name: str
    entity_id: str
    room: str | None


class ListLightsResult(BaseModel):
    lights: list[LightInfo]


@MCP.tool(description="List all configured lights with their entity_id and the room they belong to. Optionally filter by room.")
async def list_lights(room: str | None = None) -> ListLightsResult:
    light_to_room: dict[str, str] = {}
    for room_key, room_cfg in utils.CONFIG.rooms.items():
        for light_key in room_cfg.lights:
            light_to_room[light_key] = room_key

    out: list[LightInfo] = []
    for key, light in utils.CONFIG.lights.items():
        owner = light_to_room.get(key)
        if room is not None and owner != room:
            continue
        out.append(LightInfo(name=key, entity_id=light.entity_id, room=owner))
    return ListLightsResult(lights=out)
