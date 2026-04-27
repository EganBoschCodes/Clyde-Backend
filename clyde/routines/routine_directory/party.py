from typing import ClassVar

from home_assistant_lib import RGB

from ...utils import hue_to_rgb
from ..transitional_palette import TransitionalPaletteRoutine


PALETTE_SIZE = 7


class Party(TransitionalPaletteRoutine):
    NAME: ClassVar[str] = "party"
    tick_interval: ClassVar[float] = 0.4
    PALETTE: ClassVar[tuple[RGB, ...]] = tuple(hue_to_rgb(i / PALETTE_SIZE) for i in range(PALETTE_SIZE))
    PAUSE_RANGE: ClassVar[tuple[float, float]] = (0.4, 0.4)
    TRANSITION_RANGE: ClassVar[tuple[float, float]] = (0.0, 0.0)
