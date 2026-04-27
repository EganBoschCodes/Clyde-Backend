from typing import ClassVar

from home_assistant_lib import RGB

from ...utils import hex_to_rgb
from ..transitional_palette import TransitionalPaletteRoutine


class Disco(TransitionalPaletteRoutine):
    NAME: ClassVar[str] = "disco"
    tick_interval: ClassVar[float] = 0.1
    PALETTE: ClassVar[tuple[RGB, ...]] = tuple(hex_to_rgb(h) for h in (
        "#FF8C00",
        "#87CEFA",
        "#FF69B4",
        "#A020F0",
        "#FFFFFF",
    ))
    PAUSE_RANGE: ClassVar[tuple[float, float]] = (0.7, 1.3)
    TRANSITION_RANGE: ClassVar[tuple[float, float]] = (0.3, 0.3)
