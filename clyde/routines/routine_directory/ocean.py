import random
from datetime import datetime
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from ..types import LightRoutine


TICK_INTERVAL = 0.25
PALETTE: tuple[RGB, ...] = (
    (20, 110, 70),
    (40, 140, 90),
    (30, 150, 120),
    (20, 170, 160),
    (30, 180, 200),
    (20, 130, 190),
    (25, 90, 180),
    (15, 55, 150),
    (10, 35, 120),
)
TRANSITION_MIN_S = 2.0
TRANSITION_MAX_S = 4.0
BRIGHTNESS_MIN = 128
BRIGHTNESS_MAX = 255


class Ocean(LightRoutine):
    NAME: ClassVar[str] = "ocean"
    tick_interval: ClassVar[float] = TICK_INTERVAL

    def __init__(self) -> None:
        self.rng = random.Random()
        self.next_swap: dict[str, float] = {}
        self.last_color: dict[str, RGB] = {}
        self.elapsed = 0.0

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        frame: dict[str, LightOnPayload] = {}
        for key in lights:
            due = self.next_swap.get(key)
            if due is not None and self.elapsed < due:
                continue

            prior = self.last_color.get(key)
            choices = tuple(c for c in PALETTE if c != prior) if prior is not None else PALETTE
            color = self.rng.choice(choices)
            transition = self.rng.uniform(TRANSITION_MIN_S, TRANSITION_MAX_S)
            brightness = self.rng.randint(BRIGHTNESS_MIN, BRIGHTNESS_MAX)

            self.last_color[key] = color
            # Stagger first-tick swaps so lights don't re-sync after a full cycle.
            start_offset = self.rng.uniform(0.0, TRANSITION_MAX_S) if due is None else 0.0
            self.next_swap[key] = self.elapsed + start_offset + transition

            if start_offset > 0.0:
                # Skip this first emission so the light starts its own cadence later.
                continue

            frame[key] = LightOnPayload(rgb_color=color, brightness=brightness, transition=transition)

        self.elapsed += TICK_INTERVAL
        return frame
