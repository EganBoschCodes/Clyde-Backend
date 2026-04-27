from typing import ClassVar

from home_assistant_lib import RGB

from ...utils import hex_to_rgb
from ..jitter import JitterRoutine


class Candle(JitterRoutine):
    NAME: ClassVar[str] = "candle"
    tick_interval: ClassVar[float] = 0.4
    BASES: ClassVar[tuple[RGB, ...]] = (hex_to_rgb("#FF9329"),)
    JITTER: ClassVar[int] = 6
    BRIGHTNESS_RANGE: ClassVar[tuple[int, int]] = (179, 255)
