from pydantic import BaseModel, Field

from clyde.routines.custom.types import CustomRoutineSpec
from clyde.scheduler.types import ScheduledEvent


class Pin(BaseModel):
    on: bool
    rgb_color: tuple[int, int, int] | None = None
    brightness: int | None = None


class RoomState(BaseModel):
    active_routine: str | None = None
    dim_factor: float = 1.0
    pins: dict[str, Pin] = Field(default_factory=dict)


class PersistedState(BaseModel):
    schedules: list[ScheduledEvent] = Field(default_factory=list)
    rooms: dict[str, RoomState] = Field(default_factory=dict)
    custom_routines: dict[str, CustomRoutineSpec] = Field(default_factory=dict)
