import asyncio
import random
from typing import ClassVar

from home_assistant_lib import Light, LightOffPayload, LightOnPayload

from clyde.routines.types import LightRoutine
from clyde.utils import hex_to_rgb

from ..types import Event, EventContext


YELLOW = hex_to_rgb("#FFC800")
RED = hex_to_rgb("#FF0000")
GREEN = hex_to_rgb("#00FF00")
BRIGHTNESS = 255

INITIAL_HOLD_S = 1.0
SPIN_FAST_S = 0.08
SPIN_SLOW_S = 0.55
SPIN_MIN_TOTAL_S = 4.0
SPIN_MAX_TOTAL_S = 8.0
SPIN_EASE_EXP = 0.6
FINAL_HOLD_S = 3.0


def spin_schedule(total: float) -> list[float]:
    delays: list[float] = []
    running = 0.0
    while running < total:
        t = running / total
        delay = SPIN_FAST_S + (SPIN_SLOW_S - SPIN_FAST_S) * t**SPIN_EASE_EXP
        delays.append(delay)
        running += delay
    return delays


class Roulette(Event):
    NAME: ClassVar[str] = "roulette"

    async def run(self, ctx: EventContext) -> LightRoutine | None:
        rng = random.Random()
        ordered: list[tuple[str, Light]] = list(ctx.lights.items())
        if not ordered:
            return None

        yellow_payload = LightOnPayload(rgb_color=YELLOW, brightness=BRIGHTNESS, transition=0.0)
        off_payload = LightOffPayload(transition=0.0)

        # Clear the room.
        for _, light in ordered:
            await asyncio.to_thread(light.off, off_payload)

        # Flash every light yellow to open, then clear before the spin.
        for key, _ in ordered:
            await ctx.turn_on(key, yellow_payload)
        await asyncio.sleep(INITIAL_HOLD_S)
        for _, light in ordered:
            await asyncio.to_thread(light.off, off_payload)

        # Spin: decelerating pass around the room, landing on a random light.
        start = rng.randrange(len(ordered))
        await ctx.turn_on(ordered[start][0], yellow_payload)
        delays = spin_schedule(rng.uniform(SPIN_MIN_TOTAL_S, SPIN_MAX_TOTAL_S))
        current = start
        for delay in delays:
            await asyncio.to_thread(ordered[current][1].off, off_payload)
            current = (current + 1) % len(ordered)
            await ctx.turn_on(ordered[current][0], yellow_payload)
            await asyncio.sleep(delay)

        # Land: clear the spinner, flash result across the room.
        await asyncio.to_thread(ordered[current][1].off, off_payload)
        result_color = rng.choice((RED, GREEN))
        result_payload = LightOnPayload(rgb_color=result_color, brightness=BRIGHTNESS, transition=0.0)
        for key, _ in ordered:
            await ctx.turn_on(key, result_payload)
        await asyncio.sleep(FINAL_HOLD_S)

        return None
