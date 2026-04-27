from typing import ClassVar

from home_assistant_lib import RGB

from ...utils import hex_to_rgb
from ..transitional_palette import TransitionalPaletteRoutine


class Forest(TransitionalPaletteRoutine):
    NAME: ClassVar[str] = "forest"
    tick_interval: ClassVar[float] = 0.25
    PALETTE: ClassVar[tuple[RGB, ...]] = tuple(hex_to_rgb(h) for h in (
        "#1B3A1B",
        "#2D5A2D",
        "#3F7A2E",
        "#5A8C3A",
        "#7AA84A",
        "#A8B84A",
        "#6B8E23",
        "#4A6B1F",
        "#2F4F1A",
    ))
    PAUSE_RANGE: ClassVar[tuple[float, float]] = (0.5, 1.5)
    TRANSITION_RANGE: ClassVar[tuple[float, float]] = (3.0, 6.0)
