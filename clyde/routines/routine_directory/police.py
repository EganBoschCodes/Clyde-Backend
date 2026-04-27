from datetime import datetime
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from ...utils import hex_to_rgb
from ..types import LightRoutine


TICK_INTERVAL = 0.15
BRIGHTNESS = 255
RED: RGB = hex_to_rgb("#FF0000")
BLUE: RGB = hex_to_rgb("#0000FF")


class Police(LightRoutine):
    NAME: ClassVar[str] = "police"
    tick_interval: ClassVar[float] = TICK_INTERVAL

    def __init__(self) -> None:
        self.tick = 0

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        color = RED if self.tick % 2 == 0 else BLUE
        payload = LightOnPayload(rgb_color=color, brightness=BRIGHTNESS, transition=0)
        self.tick += 1
        return {light: payload for light in lights}
