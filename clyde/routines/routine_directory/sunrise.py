from datetime import datetime
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from ..types import LightRoutine


TICK_INTERVAL = 5.0
STEPS = 120
START_RGB: RGB = (255, 140, 40)
END_RGB: RGB = (255, 244, 229)
START_BRIGHTNESS = 3
END_BRIGHTNESS = 255


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def lerp_rgb(a: RGB, b: RGB, t: float) -> RGB:
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t))


class Sunrise(LightRoutine):
    NAME: ClassVar[str] = "sunrise"
    tick_interval: ClassVar[float] = TICK_INTERVAL

    def __init__(self) -> None:
        self.tick = 0

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        t = min(self.tick / STEPS, 1.0)
        rgb = lerp_rgb(START_RGB, END_RGB, t)
        brightness = lerp(START_BRIGHTNESS, END_BRIGHTNESS, t)
        payload = LightOnPayload(rgb_color=rgb, brightness=brightness, transition=TICK_INTERVAL)
        self.tick += 1
        return {light: payload for light in lights}
