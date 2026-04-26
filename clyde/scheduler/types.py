from datetime import time

from pydantic import BaseModel, field_validator


class ScheduledEvent(BaseModel):
    model_config = {"frozen": True}

    event: str
    room: str
    time: str
    days_of_week: tuple[int, ...]

    @field_validator("time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        time.fromisoformat(v)
        return v

    @field_validator("days_of_week")
    @classmethod
    def validate_days_of_week(cls, v: tuple[int, ...]) -> tuple[int, ...]:
        if not v:
            raise ValueError("days_of_week must include at least one day")
        for d in v:
            if d < 0 or d > 6:
                raise ValueError(f"day {d} out of range; expected 0 (Mon) - 6 (Sun)")
        deduped = sorted(set(v))
        if len(deduped) != len(v):
            raise ValueError("days_of_week must not contain duplicates")
        return tuple(deduped)

    def time_of_day(self) -> time:
        return time.fromisoformat(self.time)

    def runs_on(self, weekday: int) -> bool:
        return weekday in self.days_of_week

    def key(self) -> tuple[str, str, str]:
        return (self.event, self.room, self.time)
