from collections import deque
from datetime import datetime
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from ...utils import hex_to_rgb
from ..transitional_palette import TransitionalPaletteRoutine


TICK_INTERVAL = 0.15

GHOST_MIN_GAP_S = 8.0
GHOST_MAX_GAP_S = 25.0
GHOST_DIM_TRANSITION_S = 0.5
GHOST_DIM_HOLD_TICKS = 3
GHOST_FLICKER_MIN_TICKS = 4
GHOST_FLICKER_MAX_TICKS = 8
GHOST_GREEN_PROB = 0.5
GHOST_GREEN_HOLD_TICKS = 2
GHOST_LOW_BRIGHTNESS = 12
GHOST_HIGH_BRIGHTNESS = 130
GHOST_FLASH_BRIGHTNESS = 210
RECOVER_TRANSITION_S = 1.2

LIGHTNING_MIN_GAP_S = 40.0
LIGHTNING_MAX_GAP_S = 120.0
LIGHTNING_MIN_FLASHES = 2
LIGHTNING_MAX_FLASHES = 4
LIGHTNING_DARK_BRIGHTNESS = 20

GHOST_PALE: tuple[RGB, ...] = (hex_to_rgb("#B9A8FF"), hex_to_rgb("#7CFFB0"), hex_to_rgb("#8A5CFF"))
GHOST_GREEN: RGB = hex_to_rgb("#39FF14")
GHOST_DIM_COLOR: RGB = hex_to_rgb("#3A0A6B")
LIGHTNING_COLORS: tuple[RGB, ...] = (hex_to_rgb("#D8CCFF"), hex_to_rgb("#EEE8FF"))
LIGHTNING_DARK_COLOR: RGB = hex_to_rgb("#2A0A55")


class Halloween(TransitionalPaletteRoutine):
    NAME: ClassVar[str] = "halloween"
    tick_interval: ClassVar[float] = TICK_INTERVAL
    PALETTE: ClassVar[tuple[RGB, ...]] = tuple(hex_to_rgb(h) for h in (
        "#FF6A00",
        "#FF8C1A",
        "#E85D04",
        "#FFA033",
        "#6A0DAD",
        "#8A2BE2",
        "#9B30FF",
        "#4B0082",
        "#7FFF00",
    ))
    PAUSE_RANGE: ClassVar[tuple[float, float]] = (0.5, 3.0)
    TRANSITION_RANGE: ClassVar[tuple[float, float]] = (2.0, 4.5)

    def __init__(self) -> None:
        super().__init__()
        self.ghosts: dict[str, deque[LightOnPayload | None]] = {}
        self.recover: set[str] = set()
        self.lightning: deque[dict[str, LightOnPayload]] = deque()
        self.lightning_recover = False
        self.next_ghost_at: float | None = None
        self.next_lightning_at: float | None = None

    def build_ghost(self) -> deque[LightOnPayload | None]:
        seq: deque[LightOnPayload | None] = deque()
        # Dim to a faint violet and hold while the transition plays out
        seq.append(LightOnPayload(rgb_color=GHOST_DIM_COLOR, brightness=GHOST_LOW_BRIGHTNESS, transition=GHOST_DIM_TRANSITION_S))
        for _ in range(GHOST_DIM_HOLD_TICKS):
            seq.append(None)
        # Rapid flicker
        pale = self.rng.choice(GHOST_PALE)
        for i in range(self.rng.randint(GHOST_FLICKER_MIN_TICKS, GHOST_FLICKER_MAX_TICKS)):
            brightness = GHOST_HIGH_BRIGHTNESS if i % 2 == 0 else GHOST_LOW_BRIGHTNESS
            seq.append(LightOnPayload(rgb_color=pale, brightness=brightness, transition=0.0))
        # Occasional eerie green flash, then a beat of near-darkness
        if self.rng.random() < GHOST_GREEN_PROB:
            seq.append(LightOnPayload(rgb_color=GHOST_GREEN, brightness=GHOST_FLASH_BRIGHTNESS, transition=0.0))
            for _ in range(GHOST_GREEN_HOLD_TICKS):
                seq.append(None)
        seq.append(LightOnPayload(rgb_color=GHOST_DIM_COLOR, brightness=1, transition=0.0))
        return seq

    def recovery_payload(self, key: str) -> LightOnPayload | None:
        color = self.last_color.get(key)
        if color is None:
            return None
        return LightOnPayload(rgb_color=color, brightness=self.BRIGHTNESS, transition=RECOVER_TRANSITION_S)

    def queue_lightning(self, lights: list[str]) -> None:
        dark = LightOnPayload(rgb_color=LIGHTNING_DARK_COLOR, brightness=LIGHTNING_DARK_BRIGHTNESS, transition=0.0)
        flashes = self.rng.randint(LIGHTNING_MIN_FLASHES, LIGHTNING_MAX_FLASHES)
        for _ in range(flashes):
            flash = LightOnPayload(rgb_color=self.rng.choice(LIGHTNING_COLORS), brightness=255, transition=0.0)
            subset = {k for k in lights if self.rng.random() < 0.7} or {self.rng.choice(lights)}
            self.lightning.append({k: flash if k in subset else dark for k in lights})
            self.lightning.append({k: dark for k in lights})
        self.lightning_recover = True

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        frame = await super().step(now, lights)
        if not lights:
            return frame
        if self.next_ghost_at is None:
            self.next_ghost_at = self.elapsed + self.rng.uniform(GHOST_MIN_GAP_S, GHOST_MAX_GAP_S) / 2
        if self.next_lightning_at is None:
            self.next_lightning_at = self.elapsed + self.rng.uniform(LIGHTNING_MIN_GAP_S, LIGHTNING_MAX_GAP_S)

        # Room-wide lightning overrides everything until it finishes, then the room recovers
        if self.lightning:
            return self.lightning.popleft()
        if self.lightning_recover:
            self.lightning_recover = False
            recovered = {k: p for k in lights if (p := self.recovery_payload(k)) is not None}
            return {**frame, **recovered}
        if self.elapsed >= self.next_lightning_at:
            self.next_lightning_at = self.elapsed + self.rng.uniform(LIGHTNING_MIN_GAP_S, LIGHTNING_MAX_GAP_S)
            self.queue_lightning(lights)
            return self.lightning.popleft()

        # Lights whose ghost just ended fade back to their palette color
        for key in list(self.recover):
            self.recover.discard(key)
            payload = self.recovery_payload(key)
            if payload is not None and key not in self.ghosts:
                frame[key] = payload

        # A ghost owns its light: drop drift payloads and play its sequence
        for key in list(self.ghosts):
            frame.pop(key, None)
            step = self.ghosts[key].popleft()
            if step is not None:
                frame[key] = step
            if not self.ghosts[key]:
                del self.ghosts[key]
                self.recover.add(key)

        # Start a new ghost on a random lamp that isn't already haunted
        if self.elapsed >= self.next_ghost_at:
            self.next_ghost_at = self.elapsed + self.rng.uniform(GHOST_MIN_GAP_S, GHOST_MAX_GAP_S)
            free = [k for k in lights if k not in self.ghosts]
            if free:
                key = self.rng.choice(free)
                ghost = self.build_ghost()
                opening = ghost.popleft()
                assert opening is not None, "ghost sequence must open with a payload"
                self.ghosts[key] = ghost
                frame[key] = opening
        return frame
