import asyncio
from typing import ClassVar

from home_assistant_lib import LightOffPayload, LightOnPayload

from clyde.routines.types import LightRoutine

from ..types import Event, EventContext


COLOR = (0, 128, 255)
BRIGHTNESS = 255
STAGGER = 0.2
HOLD = 2.0


class ColorWipe(Event):
    NAME: ClassVar[str] = "color_wipe"

    async def run(self, ctx: EventContext) -> LightRoutine | None:
        on_payload = LightOnPayload(rgb_color=COLOR, brightness=BRIGHTNESS, transition=0.0)
        off_payload = LightOffPayload(transition=0.0)
        ordered = list(ctx.lights.items())
        for key, _ in ordered:
            await ctx.turn_on(key, on_payload)
            await asyncio.sleep(STAGGER)
        await asyncio.sleep(HOLD)
        for _, light in ordered:
            await asyncio.to_thread(light.off, off_payload)
            await asyncio.sleep(STAGGER)
