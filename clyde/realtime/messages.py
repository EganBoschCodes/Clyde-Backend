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


class LightOnEvent(BaseModel):
    type: Literal["light_on"] = "light_on"
    room: str
    light: str
    rgb_color: tuple[int, int, int] | None
    brightness: int | None
    transition: float | None


type RealtimeEvent = RoomStateEvent | RoomDimEvent | LightOnEvent
