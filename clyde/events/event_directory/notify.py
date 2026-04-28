import asyncio
from typing import ClassVar

from home_assistant_lib import LightOffPayload, LightOnPayload

from clyde.routines.types import LightRoutine
from clyde.utils import hex_to_rgb

from ..types import Event, EventContext


FLASHES = 3
ON_DURATION = 0.4
OFF_DURATION = 0.4
COLOR = hex_to_rgb("#FF0000")
BRIGHTNESS = 255


class Notify(Event):
    NAME: ClassVar[str] = "notify"

    async def run(self, ctx: EventContext) -> LightRoutine | None:
        on_payload = LightOnPayload(rgb_color=COLOR, brightness=BRIGHTNESS, transition=0.0)
        off_payload = LightOffPayload(transition=0.0)
        for _ in range(FLASHES):
            for key in ctx.lights.keys():
                await ctx.turn_on(key, on_payload)
            await asyncio.sleep(ON_DURATION)
            for light in ctx.lights.values():
                await light.off(off_payload)
            await asyncio.sleep(OFF_DURATION)
