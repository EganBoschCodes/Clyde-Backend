import colorsys
import random
from datetime import datetime
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from ..types import LightRoutine


TICK_INTERVAL = 0.1
TRANSITION = 5.0
SWAP_INTERVAL = 1.0
SATURATION = 0.25
VALUE = 1.0


class Iridescent(LightRoutine):
    NAME: ClassVar[str] = "iridescent"
    tick_interval: ClassVar[float] = TICK_INTERVAL

    def __init__(self) -> None:
        self.rng = random.Random()
        self.next_swap: dict[str, float] = {}
        self.elapsed = 0.0

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        frame: dict[str, LightOnPayload] = {}
        for key in lights:
            due = self.next_swap.get(key)
            if due is not None and self.elapsed < due:
                continue

            r, g, b = colorsys.hsv_to_rgb(self.rng.random(), SATURATION, VALUE)
            color: RGB = (int(r * 255), int(g * 255), int(b * 255))
            # Stagger first-tick swaps so lights drift out of sync.
            start_offset = self.rng.uniform(0.0, SWAP_INTERVAL) if due is None else 0.0
            self.next_swap[key] = self.elapsed + start_offset + SWAP_INTERVAL

            frame[key] = LightOnPayload(rgb_color=color, brightness=255, transition=TRANSITION)

        self.elapsed += TICK_INTERVAL
        return frame
