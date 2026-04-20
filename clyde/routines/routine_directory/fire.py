import random
from datetime import datetime
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from ..types import LightRoutine


TICK_INTERVAL = 0.12
BASES: tuple[RGB, ...] = (
    (255, 40, 0),
    (255, 80, 0),
    (255, 120, 20),
    (255, 160, 40),
)
JITTER = 15
BRIGHTNESS_MIN = 100
BRIGHTNESS_MAX = 255


def clamp(v: int) -> int:
    return max(0, min(255, v))


class Fire(LightRoutine):
    NAME: ClassVar[str] = "fire"
    tick_interval: ClassVar[float] = TICK_INTERVAL

    def __init__(self) -> None:
        self.rng = random.Random()

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        frame: dict[str, LightOnPayload] = {}
        for key in lights:
            base = self.rng.choice(BASES)
            rgb: RGB = (
                clamp(base[0] + self.rng.randint(-JITTER, JITTER)),
                clamp(base[1] + self.rng.randint(-JITTER, JITTER)),
                clamp(base[2] + self.rng.randint(-JITTER, JITTER)),
            )
            brightness = self.rng.randint(BRIGHTNESS_MIN, BRIGHTNESS_MAX)
            frame[key] = LightOnPayload(rgb_color=rgb, brightness=brightness, transition=TICK_INTERVAL)
        return frame
