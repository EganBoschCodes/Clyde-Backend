from typing import ClassVar

from home_assistant_lib import RGB

from ...utils import hex_to_rgb
from ..transitional_palette import TransitionalPaletteRoutine


class Sunset(TransitionalPaletteRoutine):
    NAME: ClassVar[str] = "sunset"
    tick_interval: ClassVar[float] = 0.25
    PALETTE: ClassVar[tuple[RGB, ...]] = tuple(hex_to_rgb(h) for h in (
        "#FFB450",
        "#FF7828",
        "#FF5A3C",
        "#FF648C",
        "#FF96AA",
        "#E6465A",
        "#DC3278",
        "#C83CA0",
        "#AA46C8",
        "#8232BE",
        "#3C1450",
    ))
    PAUSE_RANGE: ClassVar[tuple[float, float]] = (0.0, 0.0)
    TRANSITION_RANGE: ClassVar[tuple[float, float]] = (4.0, 8.0)
