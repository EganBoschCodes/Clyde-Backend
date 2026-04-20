from bisect import bisect_right
from datetime import datetime, time
from typing import ClassVar

from home_assistant_lib import RGB, LightOnPayload

from ..types import LightRoutine


KEYFRAMES: tuple[tuple[time, RGB], ...] = (
    (time(0, 0), (255, 130, 60)),
    (time(6, 0), (220, 230, 255)),
    (time(9, 0), (240, 250, 255)),
    (time(12, 0), (255, 255, 255)),
    (time(17, 0), (255, 230, 190)),
    (time(20, 0), (255, 170, 100)),
    (time(23, 59), (255, 130, 60)),
)
BRIGHTNESS = 255
TICK_INTERVAL = 60.0
TRANSITION = 60.0
SECONDS_PER_DAY = 86400


def time_to_seconds(t: time) -> int:
    return t.hour * 3600 + t.minute * 60 + t.second


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def lerp_rgb(a: RGB, b: RGB, t: float) -> RGB:
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t))


def current_color(now: datetime) -> RGB:
    seconds_now = now.hour * 3600 + now.minute * 60 + now.second
    boundaries = tuple(time_to_seconds(t) for t, _ in KEYFRAMES)
    idx = bisect_right(boundaries, seconds_now) - 1
    start_s = boundaries[idx]
    start_rgb = KEYFRAMES[idx][1]
    if idx + 1 < len(KEYFRAMES):
        end_s = boundaries[idx + 1]
        end_rgb = KEYFRAMES[idx + 1][1]
    else:
        end_s = SECONDS_PER_DAY
        end_rgb = KEYFRAMES[0][1]
    span = end_s - start_s
    if span == 0:
        return start_rgb
    t = (seconds_now - start_s) / span
    return lerp_rgb(start_rgb, end_rgb, t)


class Daylight(LightRoutine):
    NAME: ClassVar[str] = "daylight"
    tick_interval: ClassVar[float] = TICK_INTERVAL

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        color = current_color(now)
        payload = LightOnPayload(rgb_color=color, brightness=BRIGHTNESS, transition=TRANSITION)
        return {light: payload for light in lights}
