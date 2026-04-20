from datetime import datetime
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from ..types import LightRoutine


TICK_INTERVAL = 60.0
TRANSITION = 2.0
COLOR: RGB = (255, 0, 0)
BRIGHTNESS = 5


class NightLight(LightRoutine):
    NAME: ClassVar[str] = "night_light"
    tick_interval: ClassVar[float] = TICK_INTERVAL

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        payload = LightOnPayload(rgb_color=COLOR, brightness=BRIGHTNESS, transition=TRANSITION)
        return {light: payload for light in lights}
