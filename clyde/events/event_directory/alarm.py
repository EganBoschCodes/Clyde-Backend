import asyncio
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from clyde.routines.routine_directory.daylight import Daylight
from clyde.routines.types import LightRoutine
from clyde.utils import hex_to_rgb

from ..types import Event, EventContext


STEPS = 120
TICK_INTERVAL = 5.0
START_RGB: RGB = hex_to_rgb("#FF8C28")
END_RGB: RGB = hex_to_rgb("#C8DCFF")
START_BRIGHTNESS = 3
END_BRIGHTNESS = 255


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def lerp_rgb(a: RGB, b: RGB, t: float) -> RGB:
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t))


class Alarm(Event):
    NAME: ClassVar[str] = "alarm"

    async def run(self, ctx: EventContext) -> LightRoutine | None:
        ctx.set_dim_factor(1.0)
        for tick in range(STEPS + 1):
            t = tick / STEPS
            rgb = lerp_rgb(START_RGB, END_RGB, t)
            brightness = lerp(START_BRIGHTNESS, END_BRIGHTNESS, t)
            payload = LightOnPayload(rgb_color=rgb, brightness=brightness, transition=TICK_INTERVAL)
            for key in ctx.lights.keys():
                await ctx.turn_on(key, payload)
            await asyncio.sleep(TICK_INTERVAL)
        return Daylight()
