import random
from datetime import datetime
from typing import ClassVar

from home_assistant_lib import LightOnPayload

from ..types import LightRoutine


TICK_INTERVAL = 1.0
MIN_TOGGLE_TICKS = 120
MAX_TOGGLE_TICKS = 1800
ON_BRIGHTNESS_MIN = 150
ON_BRIGHTNESS_MAX = 255


class Away(LightRoutine):
    NAME: ClassVar[str] = "away"
    tick_interval: ClassVar[float] = TICK_INTERVAL

    def __init__(self) -> None:
        self.rng = random.Random()
        self.tick = 0
        self.state: dict[str, bool] = {}
        self.next_toggle: dict[str, int] = {}

    def _init_light(self, key: str) -> None:
        self.state[key] = self.rng.random() < 0.5
        self.next_toggle[key] = self.tick + self.rng.randint(MIN_TOGGLE_TICKS, MAX_TOGGLE_TICKS)

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        frame: dict[str, LightOnPayload] = {}
        for key in lights:
            if key not in self.state:
                self._init_light(key)
            if self.tick >= self.next_toggle[key]:
                self.state[key] = not self.state[key]
                self.next_toggle[key] = self.tick + self.rng.randint(MIN_TOGGLE_TICKS, MAX_TOGGLE_TICKS)
            if self.state[key]:
                brightness = self.rng.randint(ON_BRIGHTNESS_MIN, ON_BRIGHTNESS_MAX)
                frame[key] = LightOnPayload(rgb_color=(255, 200, 150), brightness=brightness, transition=TICK_INTERVAL)
            else:
                frame[key] = LightOnPayload(rgb_color=(0, 0, 0), brightness=1, transition=TICK_INTERVAL)
        self.tick += 1
        return frame
