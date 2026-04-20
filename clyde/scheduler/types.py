from datetime import time

from pydantic import BaseModel, field_validator


class ScheduledEvent(BaseModel):
    model_config = {"frozen": True}

    event: str
    room: str
    time: str

    @field_validator("time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        time.fromisoformat(v)
        return v

    def time_of_day(self) -> time:
        return time.fromisoformat(self.time)

    def key(self) -> tuple[str, str, str]:
        return (self.event, self.room, self.time)
