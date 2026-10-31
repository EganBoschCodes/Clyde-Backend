import math
from datetime import datetime
from typing import ClassVar, assert_never

from home_assistant_lib import RGB, LightOnPayload

from ...utils import hex_to_rgb
from ..jitter import JitterRoutine
from ..transitional_palette import TransitionalPaletteRoutine
from ..types import LightRoutine
from .types import CustomRoutineSpec


DRIFT_TICK_S = 0.25
DRIFT_TRANSITION_S = (8.0, 1.5)
DRIFT_PAUSE_S = ((6.0, 10.0), (0.0, 1.0))
TRANSITION_SPREAD = 1.6
FLICKER_TICK_S = (0.3, 0.08)
FLICKER_JITTER = (8, 35)
FLICKER_MIN_BRIGHTNESS_RATIO = 0.4
PULSE_TICK_S = 0.2
PULSE_PERIOD_S = (12.0, 2.0)
PULSE_MIN_BRIGHTNESS_RATIO = 0.15
PULSE_COLOR_CYCLES_PER_PERIOD = 0.5
CHASE_STEP_S = (1.5, 0.15)
CHASE_TRANSITION_RATIO = 0.6
STATIC_TICK_S = 2.0
STATIC_REEMIT_TICKS = 15
STATIC_TRANSITION_S = 1.0


def lerp(slow: float, fast: float, speed: float) -> float:
    return slow + (fast - slow) * speed


def mix(a: RGB, b: RGB, t: float) -> RGB:
    return (round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t), round(a[2] + (b[2] - a[2]) * t))


def palette_of(spec: CustomRoutineSpec) -> tuple[RGB, ...]:
    return tuple(hex_to_rgb(c) for c in spec.colors)


class PulseRoutine(LightRoutine):
    def __init__(self, palette: tuple[RGB, ...], speed: float, brightness: int) -> None:
        self.palette = palette
        self.period = lerp(PULSE_PERIOD_S[0], PULSE_PERIOD_S[1], speed)
        self.high = brightness
        self.low = max(1, round(brightness * PULSE_MIN_BRIGHTNESS_RATIO))
        self.elapsed = 0.0

    def color_at(self) -> RGB:
        if len(self.palette) == 1:
            return self.palette[0]
        position = self.elapsed / (self.period / PULSE_COLOR_CYCLES_PER_PERIOD) * len(self.palette)
        index = int(position) % len(self.palette)
        return mix(self.palette[index], self.palette[(index + 1) % len(self.palette)], position - int(position))

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        phase = 2 * math.pi * self.elapsed / self.period
        brightness = round(self.low + (self.high - self.low) * (1 - math.cos(phase)) / 2)
        payload = LightOnPayload(rgb_color=self.color_at(), brightness=brightness, transition=PULSE_TICK_S)
        self.elapsed += PULSE_TICK_S
        return {light: payload for light in lights}


class ChaseRoutine(LightRoutine):
    def __init__(self, palette: tuple[RGB, ...], brightness: int, transition: float) -> None:
        self.palette = palette
        self.brightness = brightness
        self.transition = transition
        self.offset = 0

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        frame: dict[str, LightOnPayload] = {}
        for i, light in enumerate(lights):
            color = self.palette[(i - self.offset) % len(self.palette)]
            frame[light] = LightOnPayload(rgb_color=color, brightness=self.brightness, transition=self.transition)
        self.offset += 1
        return frame


class StaticRoutine(LightRoutine):
    def __init__(self, palette: tuple[RGB, ...], brightness: int) -> None:
        self.palette = palette
        self.brightness = brightness
        self.ticks = 0

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        due = self.ticks % STATIC_REEMIT_TICKS == 0
        self.ticks += 1
        if not due:
            return {}
        return {
            light: LightOnPayload(rgb_color=self.palette[i % len(self.palette)], brightness=self.brightness, transition=STATIC_TRANSITION_S)
            for i, light in enumerate(lights)
        }


def build_drift(key: str, spec: CustomRoutineSpec) -> LightRoutine:
    palette = palette_of(spec)
    trans_min = lerp(DRIFT_TRANSITION_S[0], DRIFT_TRANSITION_S[1], spec.speed)
    pause_min = lerp(DRIFT_PAUSE_S[0][0], DRIFT_PAUSE_S[1][0], spec.speed)
    pause_max = lerp(DRIFT_PAUSE_S[0][1], DRIFT_PAUSE_S[1][1], spec.speed)

    class CustomDrift(TransitionalPaletteRoutine):
        NAME: ClassVar[str] = key
        tick_interval: ClassVar[float] = DRIFT_TICK_S
        PALETTE: ClassVar[tuple[RGB, ...]] = palette
        PAUSE_RANGE: ClassVar[tuple[float, float]] = (pause_min, pause_max)
        TRANSITION_RANGE: ClassVar[tuple[float, float]] = (trans_min, trans_min * TRANSITION_SPREAD)
        BRIGHTNESS: ClassVar[int] = spec.brightness

    return CustomDrift()


def build_flicker(key: str, spec: CustomRoutineSpec) -> LightRoutine:
    palette = palette_of(spec)
    tick = lerp(FLICKER_TICK_S[0], FLICKER_TICK_S[1], spec.speed)
    jitter = round(lerp(FLICKER_JITTER[0], FLICKER_JITTER[1], spec.speed))
    low = max(1, round(spec.brightness * FLICKER_MIN_BRIGHTNESS_RATIO))

    class CustomFlicker(JitterRoutine):
        NAME: ClassVar[str] = key
        tick_interval: ClassVar[float] = tick
        BASES: ClassVar[tuple[RGB, ...]] = palette
        JITTER: ClassVar[int] = jitter
        BRIGHTNESS_RANGE: ClassVar[tuple[int, int]] = (low, spec.brightness)

    return CustomFlicker()


def build_pulse(key: str, spec: CustomRoutineSpec) -> LightRoutine:
    class CustomPulse(PulseRoutine):
        NAME: ClassVar[str] = key
        tick_interval: ClassVar[float] = PULSE_TICK_S

    return CustomPulse(palette_of(spec), spec.speed, spec.brightness)


def build_chase(key: str, spec: CustomRoutineSpec) -> LightRoutine:
    step_s = lerp(CHASE_STEP_S[0], CHASE_STEP_S[1], spec.speed)

    class CustomChase(ChaseRoutine):
        NAME: ClassVar[str] = key
        tick_interval: ClassVar[float] = step_s

    return CustomChase(palette_of(spec), spec.brightness, step_s * CHASE_TRANSITION_RATIO)


def build_static(key: str, spec: CustomRoutineSpec) -> LightRoutine:
    class CustomStatic(StaticRoutine):
        NAME: ClassVar[str] = key
        tick_interval: ClassVar[float] = STATIC_TICK_S

    return CustomStatic(palette_of(spec), spec.brightness)


def build_custom_routine(key: str, spec: CustomRoutineSpec) -> LightRoutine:
    match spec.style:
        case "drift":
            return build_drift(key, spec)
        case "flicker":
            return build_flicker(key, spec)
        case "pulse":
            return build_pulse(key, spec)
        case "chase":
            return build_chase(key, spec)
        case "static":
            return build_static(key, spec)
        case _ as unreachable:
            assert_never(unreachable)
