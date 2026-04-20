import random
from datetime import datetime
from typing import ClassVar

from home_assistant_lib import LightOnPayload

from ..types import LightRoutine


TICK_INTERVAL = 0.1
FLASH_PROB = 0.01
SECONDARY_PROB = 0.008


class Lightning(LightRoutine):
    NAME: ClassVar[str] = "lightning"
    tick_interval: ClassVar[float] = TICK_INTERVAL

    def __init__(self) -> None:
        self.rng = random.Random()

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        roll = self.rng.random()
        if roll < FLASH_PROB + SECONDARY_PROB:
            payload = LightOnPayload(rgb_color=(255, 255, 255), brightness=255, transition=0)
        else:
            payload = LightOnPayload(rgb_color=(0, 0, 0), brightness=1, transition=0)
        return {light: payload for light in lights}
