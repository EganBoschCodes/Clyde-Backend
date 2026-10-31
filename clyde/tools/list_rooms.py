from pydantic import BaseModel

from clyde.mcp_app import MCP
from clyde.managers import ENGINE
from clyde.state import Pin

import clyde.utils as utils


class RoomStatus(BaseModel):
    name: str
    display_name: str
    lights: list[str]
    active_routine: str | None
    active_event: str | None
    dim_factor: float
    pins: dict[str, Pin] = {}


class ListRoomsResult(BaseModel):
    rooms: list[RoomStatus]


@MCP.tool(description="List all configured rooms with their lights, currently active routine and event (if any), current dim factor, and pins (lights held out of the routine at a manual state, keyed by light). `name` is the room key; `display_name` is the human-readable name.")
async def list_rooms() -> ListRoomsResult:
    rooms: list[RoomStatus] = []
    for room_key, room in utils.CONFIG.rooms.items():
        manager = ENGINE.managers.get(room_key)
        active = manager.active.NAME if manager is not None and manager.active is not None else None
        active_event = manager.active_event.NAME if manager is not None and manager.active_event is not None else None
        dim_factor = manager.dim_factor if manager is not None else 1.0
        pins = dict(manager.pins) if manager is not None else {}
        rooms.append(RoomStatus(name=room_key, display_name=room.name, lights=list(room.lights), active_routine=active, active_event=active_event, dim_factor=dim_factor, pins=pins))
    return ListRoomsResult(rooms=rooms)
