import asyncio
from typing import ClassVar

from home_assistant_lib import LightOffPayload, LightOnPayload

from clyde.routines.types import LightRoutine
from clyde.utils import hex_to_rgb

from ..types import Event, EventContext


COLOR = hex_to_rgb("#FFC800")
BRIGHTNESS = 255
FLASH_ON = 0.2
FLASH_OFF = 0.15
PAUSE = 0.25


class Doorbell(Event):
    NAME: ClassVar[str] = "doorbell"

    async def run(self, ctx: EventContext) -> LightRoutine | None:
        on_payload = LightOnPayload(rgb_color=COLOR, brightness=BRIGHTNESS, transition=0.0)
        off_payload = LightOffPayload(transition=0.0)
        for burst in range(2):
            for _ in range(2):
                for key in ctx.lights.keys():
                    await ctx.turn_on(key, on_payload)
                await asyncio.sleep(FLASH_ON)
                for light in ctx.lights.values():
                    await asyncio.to_thread(light.off, off_payload)
                await asyncio.sleep(FLASH_OFF)
            if burst == 0:
                await asyncio.sleep(PAUSE)
