import random
from collections import deque
from datetime import datetime, timedelta
from typing import ClassVar

from home_assistant_lib import LightOnPayload

from ...utils import hex_to_rgb
from ..types import LightRoutine


TICK_INTERVAL = 0.1
MIN_INTERVAL_S = 0.5
MAX_INTERVAL_S = 10.0
SINGLE_FLASH_PROB = 0.75
PER_LIGHT_ON_PROB = 0.5
MULTI_FLASH_MIN = 2
MULTI_FLASH_MAX = 4
FLASH_ON_TICKS = 1
FLASH_GAP_TICKS = 1
MIN_BRIGHTNESS = 102
MAX_BRIGHTNESS = 255

OFF_COLOR = hex_to_rgb("#000000")
ON_COLOR = hex_to_rgb("#FFFFFF")
FLASH_OFF = LightOnPayload(rgb_color=OFF_COLOR, brightness=1, transition=0)


class Lightning(LightRoutine):
    NAME: ClassVar[str] = "lightning"
    tick_interval: ClassVar[float] = TICK_INTERVAL

    def __init__(self) -> None:
        self.rng = random.Random()
        self.queue: deque[dict[str, LightOnPayload]] = deque()
        self.next_flash_at: datetime | None = None

    def schedule_next(self, now: datetime) -> None:
        delay = self.rng.uniform(MIN_INTERVAL_S, MAX_INTERVAL_S)
        self.next_flash_at = now + timedelta(seconds=delay)

    def make_on(self) -> LightOnPayload:
        brightness = self.rng.randint(MIN_BRIGHTNESS, MAX_BRIGHTNESS)
        return LightOnPayload(rgb_color=ON_COLOR, brightness=brightness, transition=0)

    def pick_independent(self, lights: list[str]) -> set[str]:
        subset = {light for light in lights if self.rng.random() < PER_LIGHT_ON_PROB}
        if not subset:
            subset = {self.rng.choice(lights)}
        return subset

    def pick_sample(self, lights: list[str]) -> set[str]:
        k = self.rng.randint(1, len(lights))
        return set(self.rng.sample(lights, k))

    def build_burst(self, lights: list[str]) -> None:
        if self.rng.random() < SINGLE_FLASH_PROB:
            flashes = 1
        else:
            flashes = self.rng.randint(MULTI_FLASH_MIN, MULTI_FLASH_MAX)
        off_frame = {light: FLASH_OFF for light in lights}
        for i in range(flashes):
            subset = self.pick_independent(lights) if flashes == 1 else self.pick_sample(lights)
            on_payload = self.make_on()
            on_frame = {light: on_payload if light in subset else FLASH_OFF for light in lights}
            for _ in range(FLASH_ON_TICKS):
                self.queue.append(on_frame)
            if i < flashes - 1:
                for _ in range(FLASH_GAP_TICKS):
                    self.queue.append(off_frame)

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        if self.next_flash_at is None:
            self.schedule_next(now)

        if self.queue:
            return self.queue.popleft()

        if self.next_flash_at is not None and now >= self.next_flash_at:
            self.build_burst(lights)
            self.schedule_next(now)
            if self.queue:
                return self.queue.popleft()

        return {light: FLASH_OFF for light in lights}
