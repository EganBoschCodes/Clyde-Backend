from typing import ClassVar

from home_assistant_lib import RGB

from ...utils import hex_to_rgb
from ..transitional_palette import TransitionalPaletteRoutine


class Ocean(TransitionalPaletteRoutine):
    NAME: ClassVar[str] = "ocean"
    tick_interval: ClassVar[float] = 0.25
    PALETTE: ClassVar[tuple[RGB, ...]] = tuple(hex_to_rgb(h) for h in (
        "#146E46",
        "#288C5A",
        "#1E9678",
        "#14AAA0",
        "#1EB4C8",
        "#1482BE",
        "#195AB4",
        "#0F3796",
        "#0A2378",
    ))
    PAUSE_RANGE: ClassVar[tuple[float, float]] = (0.0, 0.0)
    TRANSITION_RANGE: ClassVar[tuple[float, float]] = (2.0, 4.0)
