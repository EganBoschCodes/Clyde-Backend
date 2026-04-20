from abc import ABC, abstractmethod
from datetime import datetime
from typing import ClassVar

from home_assistant_lib import LightOnPayload


class LightRoutine(ABC):
    NAME: ClassVar[str]
    tick_interval: ClassVar[float]

    @abstractmethod
    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        ...
