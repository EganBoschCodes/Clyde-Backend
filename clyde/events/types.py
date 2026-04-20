from abc import ABC, abstractmethod
from typing import ClassVar

from home_assistant_lib import Light


class EventContext:
    def __init__(self, lights: dict[str, Light]) -> None:
        self.lights = lights


class Event(ABC):
    NAME: ClassVar[str]

    @abstractmethod
    async def run(self, ctx: EventContext) -> None:
        ...
