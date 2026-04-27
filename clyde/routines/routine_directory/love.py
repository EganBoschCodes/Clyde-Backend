from typing import ClassVar

from home_assistant_lib import RGB

from ...utils import hex_to_rgb
from ..transitional_palette import TransitionalPaletteRoutine


class Love(TransitionalPaletteRoutine):
    NAME: ClassVar[str] = "love"
    tick_interval: ClassVar[float] = 0.25
    PALETTE: ClassVar[tuple[RGB, ...]] = tuple(hex_to_rgb(h) for h in (
        "#FFB4D2",
        "#FF82B4",
        "#FF5096",
        "#E6286E",
        "#DC1446",
        "#C81E32",
        "#B41450",
        "#A0288C",
        "#821EAA",
        "#5A1496",
        "#320A5A",
    ))
    PAUSE_RANGE: ClassVar[tuple[float, float]] = (0.0, 0.0)
    TRANSITION_RANGE: ClassVar[tuple[float, float]] = (4.0, 8.0)
