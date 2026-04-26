import asyncio
from typing import ClassVar

from home_assistant_lib import LightOffPayload, LightOnPayload

from clyde.routines.types import LightRoutine

from ..types import Event, EventContext


FLASHES = 3
ON_DURATION = 0.4
OFF_DURATION = 0.4
COLOR = (255, 0, 0)
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
                await asyncio.to_thread(light.off, off_payload)
            await asyncio.sleep(OFF_DURATION)
