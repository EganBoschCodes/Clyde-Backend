import random
from datetime import datetime
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from ..types import LightRoutine


TICK_INTERVAL = 0.1
TRANSITION = 0.3
SWAP_MIN_S = 0.7
SWAP_MAX_S = 1.3
PALETTE: tuple[RGB, ...] = (
    (255, 140, 0),
    (135, 206, 250),
    (255, 105, 180),
    (160, 32, 240),
    (255, 255, 255),
)


class Disco(LightRoutine):
    NAME: ClassVar[str] = "disco"
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
            hold = self.rng.uniform(SWAP_MIN_S, SWAP_MAX_S)

            self.last_color[key] = color
            # Stagger first-tick swaps so lights drift out of sync.
            start_offset = self.rng.uniform(0.0, SWAP_MAX_S) if due is None else 0.0
            self.next_swap[key] = self.elapsed + start_offset + hold

            frame[key] = LightOnPayload(rgb_color=color, brightness=255, transition=TRANSITION)

        self.elapsed += TICK_INTERVAL
        return frame
