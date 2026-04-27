import random
from datetime import datetime
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from .types import LightRoutine


def clamp(v: int) -> int:
    return max(0, min(255, v))


class JitterRoutine(LightRoutine):
    BASES: ClassVar[tuple[RGB, ...]]
    JITTER: ClassVar[int]
    BRIGHTNESS_RANGE: ClassVar[tuple[int, int]]

    def __init__(self) -> None:
        self.rng = random.Random()

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        frame: dict[str, LightOnPayload] = {}
        bmin, bmax = self.BRIGHTNESS_RANGE
        for key in lights:
            base = self.rng.choice(self.BASES)
            rgb: RGB = (
                clamp(base[0] + self.rng.randint(-self.JITTER, self.JITTER)),
                clamp(base[1] + self.rng.randint(-self.JITTER, self.JITTER)),
                clamp(base[2] + self.rng.randint(-self.JITTER, self.JITTER)),
            )
            brightness = self.rng.randint(bmin, bmax)
            frame[key] = LightOnPayload(rgb_color=rgb, brightness=brightness, transition=self.tick_interval)
        return frame
