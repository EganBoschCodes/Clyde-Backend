import random
from datetime import datetime, timedelta
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from ...utils import hex_to_rgb
from ..types import LightRoutine


TICK_INTERVAL = 0.1

BASE_COLOR: RGB = hex_to_rgb("#FF4A14")
BASE_BRIGHTNESS = 153

SPARK_BRIGHT_COLOR: RGB = hex_to_rgb("#FFE680")
SPARK_DIM_COLOR: RGB = hex_to_rgb("#FFA000")
SPARK_BRIGHT_LEVEL = 255
SPARK_DIM_LEVEL = 110

FLICKER_INTERVAL_MIN_S = 3.0
FLICKER_INTERVAL_MAX_S = 5.0
FLICKER_BRIGHTNESS_SEQUENCE: tuple[int, ...] = (30, 130, 10, 90)
FLICKER_DURATION_TICKS = len(FLICKER_BRIGHTNESS_SEQUENCE)
FLICKER_TRANSITION = TICK_INTERVAL

SPARK_INTERVAL_MIN_S = 7.0
SPARK_INTERVAL_MAX_S = 14.0
SPARK_DURATION_TICKS = 5
SPARK_HALF_PERIOD_TICKS = 1
SPARK_TRANSITION = TICK_INTERVAL

BASE_PAYLOAD = LightOnPayload(rgb_color=BASE_COLOR, brightness=BASE_BRIGHTNESS, transition=TICK_INTERVAL)
SPARK_BRIGHT_PAYLOAD = LightOnPayload(rgb_color=SPARK_BRIGHT_COLOR, brightness=SPARK_BRIGHT_LEVEL, transition=SPARK_TRANSITION)
SPARK_DIM_PAYLOAD = LightOnPayload(rgb_color=SPARK_DIM_COLOR, brightness=SPARK_DIM_LEVEL, transition=SPARK_TRANSITION)


class Damage(LightRoutine):
    NAME: ClassVar[str] = "damage"
    tick_interval: ClassVar[float] = TICK_INTERVAL

    def __init__(self) -> None:
        self.rng = random.Random()
        self.next_flicker_at: datetime | None = None
        self.next_spark_at: datetime | None = None
        self.flicker_light: str | None = None
        self.flicker_ticks_left = 0
        self.spark_light: str | None = None
        self.spark_ticks_left = 0

    def schedule_flicker(self, now: datetime) -> None:
        delay = self.rng.uniform(FLICKER_INTERVAL_MIN_S, FLICKER_INTERVAL_MAX_S)
        self.next_flicker_at = now + timedelta(seconds=delay)

    def schedule_spark(self, now: datetime) -> None:
        delay = self.rng.uniform(SPARK_INTERVAL_MIN_S, SPARK_INTERVAL_MAX_S)
        self.next_spark_at = now + timedelta(seconds=delay)

    def maybe_start_flicker(self, now: datetime, lights: list[str]) -> None:
        if self.flicker_ticks_left > 0 or self.next_flicker_at is None or now < self.next_flicker_at:
            return
        candidates = [light for light in lights if light != self.spark_light]
        if candidates:
            self.flicker_light = self.rng.choice(candidates)
            self.flicker_ticks_left = FLICKER_DURATION_TICKS
        self.schedule_flicker(now)

    def maybe_start_spark(self, now: datetime, lights: list[str]) -> None:
        if self.spark_ticks_left > 0 or self.next_spark_at is None or now < self.next_spark_at:
            return
        candidates = [light for light in lights if light != self.flicker_light]
        if candidates:
            self.spark_light = self.rng.choice(candidates)
            self.spark_ticks_left = SPARK_DURATION_TICKS
        self.schedule_spark(now)

    def flicker_payload(self) -> LightOnPayload:
        elapsed = FLICKER_DURATION_TICKS - self.flicker_ticks_left
        brightness = FLICKER_BRIGHTNESS_SEQUENCE[elapsed]
        return LightOnPayload(rgb_color=BASE_COLOR, brightness=brightness, transition=FLICKER_TRANSITION)

    def spark_payload(self) -> LightOnPayload:
        elapsed = SPARK_DURATION_TICKS - self.spark_ticks_left
        phase = (elapsed // SPARK_HALF_PERIOD_TICKS) % 2
        return SPARK_BRIGHT_PAYLOAD if phase == 0 else SPARK_DIM_PAYLOAD

    def advance_timers(self) -> None:
        if self.flicker_ticks_left > 0:
            self.flicker_ticks_left -= 1
            if self.flicker_ticks_left == 0:
                self.flicker_light = None
        if self.spark_ticks_left > 0:
            self.spark_ticks_left -= 1
            if self.spark_ticks_left == 0:
                self.spark_light = None

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        if self.next_flicker_at is None:
            self.schedule_flicker(now)
        if self.next_spark_at is None:
            self.schedule_spark(now)

        self.maybe_start_flicker(now, lights)
        self.maybe_start_spark(now, lights)

        frame: dict[str, LightOnPayload] = {}
        for light in lights:
            if light == self.flicker_light and self.flicker_ticks_left > 0:
                frame[light] = self.flicker_payload()
            elif light == self.spark_light and self.spark_ticks_left > 0:
                frame[light] = self.spark_payload()
            else:
                frame[light] = BASE_PAYLOAD

        self.advance_timers()
        return frame
