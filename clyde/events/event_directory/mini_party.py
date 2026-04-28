import asyncio
import random
from typing import ClassVar

from home_assistant_lib import LightOnPayload, hue_to_rgb

from clyde.routines.types import LightRoutine

from ..types import Event, EventContext


DURATION_S = 5.0
TICK_INTERVAL = 0.2


class MiniParty(Event):
    NAME: ClassVar[str] = "mini_party"

    async def run(self, ctx: EventContext) -> LightRoutine | None:
        active: list[tuple[str, int | None]] = []
        for key, light in ctx.lights.items():
            state, error = await light.get_state()
            if error is not None or state is None:
                continue
            if not state.on:
                continue
            active.append((key, state.brightness))
        if not active:
            return
        rng = random.Random()
        ticks = int(DURATION_S / TICK_INTERVAL)
        for _ in range(ticks):
            for key, brightness in active:
                payload = LightOnPayload(rgb_color=hue_to_rgb(rng.random()), brightness=brightness, transition=0.0)
                await ctx.turn_on(key, payload)
            await asyncio.sleep(TICK_INTERVAL)
