import asyncio
import random
from typing import ClassVar

from home_assistant_lib import LightOnPayload, hue_to_rgb

from ..types import Event, EventContext


DURATION_S = 5.0
TICK_INTERVAL = 0.4
BRIGHTNESS = 255


class MiniParty(Event):
    NAME: ClassVar[str] = "mini_party"

    async def run(self, ctx: EventContext) -> None:
        rng = random.Random()
        ticks = int(DURATION_S / TICK_INTERVAL)
        for _ in range(ticks):
            for light in ctx.lights.values():
                payload = LightOnPayload(rgb_color=hue_to_rgb(rng.random()), brightness=BRIGHTNESS, transition=0.0)
                await asyncio.to_thread(light.on, payload)
            await asyncio.sleep(TICK_INTERVAL)
