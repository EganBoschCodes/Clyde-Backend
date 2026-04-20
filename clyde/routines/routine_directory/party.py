import random
from datetime import datetime
from typing import ClassVar

from home_assistant_lib import LightOnPayload, hue_to_rgb

from .types import LightRoutine


TICK_INTERVAL = 0.4
BRIGHTNESS = 255


class Party(LightRoutine):
    NAME: ClassVar[str] = "party"
    tick_interval: ClassVar[float] = TICK_INTERVAL

    def __init__(self) -> None:
        self.rng = random.Random()

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        frame: dict[str, LightOnPayload] = {}
        for key in lights:
            rgb = hue_to_rgb(self.rng.random())
            frame[key] = LightOnPayload(rgb_color=rgb, brightness=BRIGHTNESS, transition=0)
        return frame
