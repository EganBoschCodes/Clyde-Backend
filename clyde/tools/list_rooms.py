from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.managers import ENGINE

import clyde.utils as utils


class RoomStatus(BaseModel):
    name: str
    lights: list[str]
    active_routine: str | None
    dim_factor: float


class ListRoomsResult(BaseModel):
    rooms: list[RoomStatus]


@MCP.tool(description="List all configured rooms with their lights, currently active routine (if any), and current dim factor.")
async def list_rooms() -> ListRoomsResult:
    rooms: list[RoomStatus] = []
    for room_key, room in utils.CONFIG.rooms.items():
        manager = ENGINE.managers.get(room_key)
        active = manager.active.NAME if manager is not None and manager.active is not None else None
        dim_factor = manager.dim_factor if manager is not None else 1.0
        rooms.append(RoomStatus(name=room_key, lights=list(room.lights), active_routine=active, dim_factor=dim_factor))
    return ListRoomsResult(rooms=rooms)
