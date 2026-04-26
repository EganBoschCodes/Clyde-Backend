import asyncio
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import ClassVar

from home_assistant_lib import Light, LightOnPayload

import clyde.utils as utils

from clyde.realtime import BUS, LightOnEvent
from clyde.routines.types import LightRoutine


class EventContext:
    def __init__(self, room_key: str, lights: dict[str, Light], set_dim_factor: Callable[[float], utils.Result[float]]) -> None:
        self.room_key = room_key
        self.lights = lights
        self.set_dim_factor = set_dim_factor

    async def turn_on(self, light_key: str, payload: LightOnPayload) -> None:
        light = self.lights[light_key]
        await asyncio.to_thread(light.on, payload)
        BUS.publish(LightOnEvent(
            room=self.room_key,
            light=light_key,
            rgb_color=payload.rgb_color,
            brightness=payload.brightness,
            transition=payload.transition,
        ))


class Event(ABC):
    NAME: ClassVar[str]

    @abstractmethod
    async def run(self, ctx: EventContext) -> LightRoutine | None:
        ...
