import asyncio
import random
from typing import ClassVar

from home_assistant_lib import Light, LightOnPayload, hue_to_rgb

from clyde.routines.types import LightRoutine

from ..types import Event, EventContext


DURATION_S = 5.0
TICK_INTERVAL = 0.4


class MiniParty(Event):
    NAME: ClassVar[str] = "mini_party"

    async def run(self, ctx: EventContext) -> LightRoutine | None:
        active: list[tuple[Light, int | None]] = []
        for light in ctx.lights.values():
            state, error = await asyncio.to_thread(light.get_state)
            if error is not None or state is None:
                continue
            if not state.on:
                continue
            active.append((light, state.brightness))
        if not active:
            return
        rng = random.Random()
        ticks = int(DURATION_S / TICK_INTERVAL)
        for _ in range(ticks):
            for light, brightness in active:
                payload = LightOnPayload(rgb_color=hue_to_rgb(rng.random()), brightness=brightness, transition=0.0)
                await asyncio.to_thread(light.on, payload)
            await asyncio.sleep(TICK_INTERVAL)
