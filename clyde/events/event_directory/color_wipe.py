import asyncio
from typing import ClassVar

from home_assistant_lib import LightOffPayload, LightOnPayload

from ..types import Event, EventContext


COLOR = (0, 128, 255)
BRIGHTNESS = 255
STAGGER = 0.2
HOLD = 2.0


class ColorWipe(Event):
    NAME: ClassVar[str] = "color_wipe"

    async def run(self, ctx: EventContext) -> None:
        on_payload = LightOnPayload(rgb_color=COLOR, brightness=BRIGHTNESS, transition=0.0)
        off_payload = LightOffPayload(transition=0.0)
        ordered = list(ctx.lights.values())
        for light in ordered:
            await asyncio.to_thread(light.on, on_payload)
            await asyncio.sleep(STAGGER)
        await asyncio.sleep(HOLD)
        for light in ordered:
            await asyncio.to_thread(light.off, off_payload)
            await asyncio.sleep(STAGGER)
