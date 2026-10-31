import asyncio
import random
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from clyde.routines.types import LightRoutine
from clyde.utils import hex_to_rgb

from ..types import Event, EventContext


DARK_COLOR: RGB = hex_to_rgb("#1A0033")
CRAWL_COLORS: tuple[RGB, ...] = (hex_to_rgb("#39FF14"), hex_to_rgb("#8A2BE2"), hex_to_rgb("#00FF7F"))
BOO_WHITE: RGB = hex_to_rgb("#FFFFFF")
BOO_ORANGE: RGB = hex_to_rgb("#FF6A00")

FADE_TRANSITION_S = 1.0
FADE_HOLD_S = 1.2
CRAWL_TOTAL_S = 1.8
CRAWL_MAX_PER_LAMP_S = 0.45
CRAWL_BRIGHTNESS = 80
DARK_BRIGHTNESS = 2
DARKNESS_BEAT_S = 0.9
BOO_FLASH_S = 0.1
BOO_HOLD_S = 0.9
OUTRO_TRANSITION_S = 0.5


class Spooky(Event):
    NAME: ClassVar[str] = "spooky"

    async def all_on(self, ctx: EventContext, payload: LightOnPayload) -> None:
        for key in ctx.lights.keys():
            await ctx.turn_on(key, payload)

    async def run(self, ctx: EventContext) -> LightRoutine | None:
        rng = random.Random()
        keys = list(ctx.lights.keys())
        if not keys:
            return None
        dark = LightOnPayload(rgb_color=DARK_COLOR, brightness=DARK_BRIGHTNESS, transition=0.0)

        # Fade the room to near-black
        await self.all_on(ctx, LightOnPayload(rgb_color=DARK_COLOR, brightness=DARK_BRIGHTNESS, transition=FADE_TRANSITION_S))
        await asyncio.sleep(FADE_HOLD_S)

        # A stuttering glow crawls lamp to lamp
        order = rng.sample(keys, len(keys))
        per_lamp = min(CRAWL_MAX_PER_LAMP_S, CRAWL_TOTAL_S / len(order))
        for key in order:
            glow = LightOnPayload(rgb_color=rng.choice(CRAWL_COLORS), brightness=CRAWL_BRIGHTNESS, transition=0.0)
            for _ in range(2):
                await ctx.turn_on(key, glow)
                await asyncio.sleep(per_lamp * 0.3)
                await ctx.turn_on(key, dark)
                await asyncio.sleep(per_lamp * 0.2)

        # A beat of darkness
        await self.all_on(ctx, dark)
        await asyncio.sleep(DARKNESS_BEAT_S)

        # BOO
        white = LightOnPayload(rgb_color=BOO_WHITE, brightness=255, transition=0.0)
        orange = LightOnPayload(rgb_color=BOO_ORANGE, brightness=255, transition=0.0)
        await self.all_on(ctx, white)
        await asyncio.sleep(BOO_FLASH_S)
        await self.all_on(ctx, orange)
        await asyncio.sleep(BOO_FLASH_S)
        await self.all_on(ctx, white)
        await asyncio.sleep(BOO_FLASH_S)
        await self.all_on(ctx, orange)
        await asyncio.sleep(BOO_HOLD_S)

        # Fade out before the manager restores the prior state
        await self.all_on(ctx, LightOnPayload(rgb_color=BOO_ORANGE, brightness=DARK_BRIGHTNESS, transition=OUTRO_TRANSITION_S))
        await asyncio.sleep(OUTRO_TRANSITION_S)
        return None
