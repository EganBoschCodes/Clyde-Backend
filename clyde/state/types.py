from pydantic import BaseModel, Field

from clyde.scheduler.types import ScheduledEvent


class RoomState(BaseModel):
    active_routine: str | None = None
    dim_factor: float = 1.0


class PersistedState(BaseModel):
    schedules: list[ScheduledEvent] = Field(default_factory=list)
    rooms: dict[str, RoomState] = Field(default_factory=dict)
