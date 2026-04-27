from typing import ClassVar

from home_assistant_lib import RGB

from ...utils import hex_to_rgb
from ..jitter import JitterRoutine


class Fire(JitterRoutine):
    NAME: ClassVar[str] = "fire"
    tick_interval: ClassVar[float] = 0.12
    BASES: ClassVar[tuple[RGB, ...]] = tuple(hex_to_rgb(h) for h in (
        "#FF2800",
        "#FF5000",
        "#FF7814",
        "#FFA028",
    ))
    JITTER: ClassVar[int] = 15
    BRIGHTNESS_RANGE: ClassVar[tuple[int, int]] = (100, 255)
