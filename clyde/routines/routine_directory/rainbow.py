from datetime import datetime
from typing import ClassVar

from home_assistant_lib import LightOnPayload, hue_to_rgb

from .types import LightRoutine


TICK_INTERVAL = 0.2
BRIGHTNESS = 255
HUE_STEPS = 24


class Rainbow(LightRoutine):
    NAME: ClassVar[str] = "rainbow"
    tick_interval: ClassVar[float] = TICK_INTERVAL

    def __init__(self) -> None:
        self.tick = 0

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        n = max(len(lights), 1)
        frame: dict[str, LightOnPayload] = {}
        for i, key in enumerate(lights):
            hue = ((self.tick / HUE_STEPS) + (i / n)) % 1.0
            rgb = hue_to_rgb(hue)
            frame[key] = LightOnPayload(rgb_color=rgb, brightness=BRIGHTNESS, transition=TICK_INTERVAL)
        self.tick += 1
        return frame
