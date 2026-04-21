import random
from datetime import datetime
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from ..types import LightRoutine


TICK_INTERVAL = 0.4
BASE: RGB = (255, 147, 41)
JITTER = 6
BRIGHTNESS_MIN = 179
BRIGHTNESS_MAX = 255


def clamp(v: int) -> int:
    return max(0, min(255, v))


class Candle(LightRoutine):
    NAME: ClassVar[str] = "candle"
    tick_interval: ClassVar[float] = TICK_INTERVAL

    def __init__(self) -> None:
        self.rng = random.Random()

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        frame: dict[str, LightOnPayload] = {}
        for key in lights:
            rgb: RGB = (
                clamp(BASE[0] + self.rng.randint(-JITTER, JITTER)),
                clamp(BASE[1] + self.rng.randint(-JITTER, JITTER)),
                clamp(BASE[2] + self.rng.randint(-JITTER, JITTER)),
            )
            brightness = self.rng.randint(BRIGHTNESS_MIN, BRIGHTNESS_MAX)
            frame[key] = LightOnPayload(rgb_color=rgb, brightness=brightness, transition=TICK_INTERVAL)
        return frame
