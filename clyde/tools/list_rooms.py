from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.routines import ENGINE

import clyde.utils as utils


class RoomStatus(BaseModel):
    name: str
    lights: list[str]
    active_routine: str | None


class ListRoomsResult(BaseModel):
    rooms: list[RoomStatus]


@MCP.tool(description="List all configured rooms with their lights and currently active routine (if any).")
async def list_rooms() -> ListRoomsResult:
    rooms: list[RoomStatus] = []
    for room_key, room in utils.CONFIG.rooms.items():
        manager = ENGINE.managers.get(room_key)
        active = manager.active.NAME if manager is not None and manager.active is not None else None
        rooms.append(RoomStatus(name=room_key, lights=list(room.lights), active_routine=active))
    return ListRoomsResult(rooms=rooms)
