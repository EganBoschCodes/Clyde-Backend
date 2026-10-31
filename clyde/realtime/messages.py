from typing import Literal

from pydantic import BaseModel

from clyde.state.types import Pin


class RoomStateEvent(BaseModel):
    type: Literal["room_state"] = "room_state"
    room: str
    active_routine: str | None


class RoomEventEvent(BaseModel):
    type: Literal["room_event"] = "room_event"
    room: str
    active_event: str | None


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


class LightOffEvent(BaseModel):
    type: Literal["light_off"] = "light_off"
    room: str
    light: str
    transition: float | None


class LightPinEvent(BaseModel):
    type: Literal["light_pin"] = "light_pin"
    room: str
    light: str
    pin: Pin | None


type RealtimeEvent = RoomStateEvent | RoomEventEvent | RoomDimEvent | LightOnEvent | LightOffEvent | LightPinEvent
