import math
from datetime import datetime
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from ..types import LightRoutine


TICK_INTERVAL = 0.1
PERIOD_S = 4.0
MIN_BRIGHTNESS = 20
MAX_BRIGHTNESS = 220
COLOR: RGB = (255, 200, 140)


class Breathe(LightRoutine):
    NAME: ClassVar[str] = "breathe"
    tick_interval: ClassVar[float] = TICK_INTERVAL

    def __init__(self) -> None:
        self.tick = 0

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        phase = 2 * math.pi * self.tick * TICK_INTERVAL / PERIOD_S
        brightness = int(MIN_BRIGHTNESS + (MAX_BRIGHTNESS - MIN_BRIGHTNESS) * (1 + math.sin(phase)) / 2)
        payload = LightOnPayload(rgb_color=COLOR, brightness=brightness, transition=TICK_INTERVAL)
        self.tick += 1
        return {light: payload for light in lights}
