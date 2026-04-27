import random
from datetime import datetime
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from .types import LightRoutine


class TransitionalPaletteRoutine(LightRoutine):
    PALETTE: ClassVar[tuple[RGB, ...]]
    PAUSE_RANGE: ClassVar[tuple[float, float]]
    TRANSITION_RANGE: ClassVar[tuple[float, float]]
    BRIGHTNESS: ClassVar[int] = 255

    def __init__(self) -> None:
        self.rng = random.Random()
        self.next_swap: dict[str, float] = {}
        self.last_color: dict[str, RGB] = {}
        self.elapsed = 0.0

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        frame: dict[str, LightOnPayload] = {}
        pause_min, pause_max = self.PAUSE_RANGE
        trans_min, trans_max = self.TRANSITION_RANGE
        for key in lights:
            due = self.next_swap.get(key)
            if due is not None and self.elapsed < due:
                continue

            prior = self.last_color.get(key)
            # Exclude colors any other light in the room is currently showing,
            # plus this light's prior color. Fall back if the palette is too
            # small to satisfy the room-wide constraint.
            in_use: set[RGB] = {self.last_color[k] for k in lights if k != key and k in self.last_color}
            if prior is not None:
                in_use.add(prior)
            choices = tuple(c for c in self.PALETTE if c not in in_use)
            if not choices:
                choices = tuple(c for c in self.PALETTE if c != prior) if prior is not None else self.PALETTE
            color = self.rng.choice(choices)
            transition = self.rng.uniform(trans_min, trans_max)
            pause = self.rng.uniform(pause_min, pause_max)

            self.last_color[key] = color
            # Stagger first-tick swaps so lights drift out of sync.
            start_offset = self.rng.uniform(0.0, trans_max + pause_max) if due is None else 0.0
            self.next_swap[key] = self.elapsed + start_offset + transition + pause

            frame[key] = LightOnPayload(rgb_color=color, brightness=self.BRIGHTNESS, transition=transition)

        self.elapsed += self.tick_interval
        return frame
