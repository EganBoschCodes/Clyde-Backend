import asyncio
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from clyde.routines.routine_directory.daylight import Daylight
from clyde.routines.types import LightRoutine

from ..types import Event, EventContext


STEPS = 10
TICK_INTERVAL = 5.0
START_RGB: RGB = (255, 140, 40)
END_RGB: RGB = (200, 220, 255)
START_BRIGHTNESS = 3
END_BRIGHTNESS = 255


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def lerp_rgb(a: RGB, b: RGB, t: float) -> RGB:
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t))


class Sunrise(Event):
    NAME: ClassVar[str] = "sunrise"

    async def run(self, ctx: EventContext) -> LightRoutine | None:
        for tick in range(STEPS + 1):
            t = tick / STEPS
            rgb = lerp_rgb(START_RGB, END_RGB, t)
            brightness = lerp(START_BRIGHTNESS, END_BRIGHTNESS, t)
            payload = LightOnPayload(rgb_color=rgb, brightness=brightness, transition=TICK_INTERVAL)
            for light in ctx.lights.values():
                await asyncio.to_thread(light.on, payload)
            await asyncio.sleep(TICK_INTERVAL)
        return Daylight()
