from typing import ClassVar

from home_assistant_lib import RGB

from ...utils import hex_to_rgb
from ..transitional_palette import TransitionalPaletteRoutine


class Love(TransitionalPaletteRoutine):
    NAME: ClassVar[str] = "love"
    tick_interval: ClassVar[float] = 0.25
    PALETTE: ClassVar[tuple[RGB, ...]] = tuple(hex_to_rgb(h) for h in (
        "#FF82B4",
        "#FF5096",
        "#E6286E",
        "#C81E32",
        "#B41450",
        "#A0055A",
        "#821EAA",
    ))
    PAUSE_RANGE: ClassVar[tuple[float, float]] = (0.0, 0.0)
    TRANSITION_RANGE: ClassVar[tuple[float, float]] = (4.0, 8.0)
