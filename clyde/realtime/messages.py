from typing import Literal

from pydantic import BaseModel


class RoomStateEvent(BaseModel):
    type: Literal["room_state"] = "room_state"
    room: str
    active_routine: str | None


class RoomDimEvent(BaseModel):
    type: Literal["room_dim"] = "room_dim"
    room: str
    factor: float


type RealtimeEvent = RoomStateEvent | RoomDimEvent
