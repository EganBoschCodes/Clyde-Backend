import math
import random
from datetime import datetime
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from ..types import LightRoutine


TICK_INTERVAL = 0.25
# Ordered along a love spectrum (soft pink -> hot pink -> red -> deep purple)
# so neighbor-drift reads as a gradient wander.
PALETTE: tuple[RGB, ...] = (
    (255, 180, 210),
    (255, 130, 180),
    (255, 80, 150),
    (230, 40, 110),
    (220, 20, 70),
    (200, 30, 50),
    (180, 20, 80),
    (160, 40, 140),
    (130, 30, 170),
    (90, 20, 150),
    (50, 10, 90),
)
NEIGHBOR_RADIUS = 3
TRANSITION_MIN_S = 4.0
TRANSITION_MAX_S = 8.0
BRIGHTNESS_MIN = 80
BRIGHTNESS_MAX = 255
BREATHE_PERIOD_S = 30.0
BREATHE_DEPTH = 0.25
HOLD_CHANCE = 0.05
HOLD_MIN_S = 8.0
HOLD_MAX_S = 12.0
HOLD_ANCHORS: tuple[RGB, ...] = (
    (220, 20, 70),
    (130, 30, 170),
    (50, 10, 90),
)


def pick_neighbor(rng: random.Random, prior: RGB | None) -> RGB:
    if prior is None or prior not in PALETTE:
        return rng.choice(PALETTE)
    idx = PALETTE.index(prior)
    lo = max(0, idx - NEIGHBOR_RADIUS)
    hi = min(len(PALETTE), idx + NEIGHBOR_RADIUS + 1)
    choices = tuple(c for i, c in enumerate(PALETTE[lo:hi], start=lo) if i != idx)
    return rng.choice(choices)


def breathed(brightness: int, elapsed: float, phase: float) -> int:
    wave = math.sin(2 * math.pi * (elapsed / BREATHE_PERIOD_S + phase))
    adjusted = brightness * (1.0 + BREATHE_DEPTH * wave)
    return max(1, min(255, int(adjusted)))


class Love(LightRoutine):
    NAME: ClassVar[str] = "love"
    tick_interval: ClassVar[float] = TICK_INTERVAL

    def __init__(self) -> None:
        self.rng = random.Random()
        self.next_swap: dict[str, float] = {}
        self.last_color: dict[str, RGB] = {}
        self.breathe_phase: dict[str, float] = {}
        self.elapsed = 0.0

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        frame: dict[str, LightOnPayload] = {}
        for key in lights:
            due = self.next_swap.get(key)
            if due is not None and self.elapsed < due:
                continue

            if key not in self.breathe_phase:
                self.breathe_phase[key] = self.rng.random()
            phase = self.breathe_phase[key]

            # Occasional hold: park the light on a deep anchor for a beat.
            if due is not None and self.rng.random() < HOLD_CHANCE:
                color = self.rng.choice(HOLD_ANCHORS)
                hold = self.rng.uniform(HOLD_MIN_S, HOLD_MAX_S)
                brightness = breathed(
                    self.rng.randint(BRIGHTNESS_MIN, BRIGHTNESS_MAX), self.elapsed, phase
                )
                self.last_color[key] = color
                self.next_swap[key] = self.elapsed + hold
                frame[key] = LightOnPayload(
                    rgb_color=color, brightness=brightness, transition=TRANSITION_MAX_S
                )
                continue

            color = pick_neighbor(self.rng, self.last_color.get(key))
            transition = self.rng.uniform(TRANSITION_MIN_S, TRANSITION_MAX_S)
            brightness = breathed(
                self.rng.randint(BRIGHTNESS_MIN, BRIGHTNESS_MAX), self.elapsed, phase
            )

            self.last_color[key] = color
            start_offset = self.rng.uniform(0.0, TRANSITION_MAX_S) if due is None else 0.0
            self.next_swap[key] = self.elapsed + start_offset + transition

            if start_offset > 0.0:
                continue

            frame[key] = LightOnPayload(rgb_color=color, brightness=brightness, transition=transition)

        self.elapsed += TICK_INTERVAL
        return frame
