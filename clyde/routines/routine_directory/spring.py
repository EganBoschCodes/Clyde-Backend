from typing import ClassVar

from home_assistant_lib import RGB

from ...utils import hex_to_rgb
from ..transitional_palette import TransitionalPaletteRoutine


class Spring(TransitionalPaletteRoutine):
    NAME: ClassVar[str] = "spring"
    tick_interval: ClassVar[float] = 0.25
    PALETTE: ClassVar[tuple[RGB, ...]] = tuple(hex_to_rgb(h) for h in (
        "#FF8FBF",
        "#FF9FAF",
        "#FFB28A",
        "#FFD470",
        "#C8EC78",
        "#7ADCA0",
        "#7ACFCF",
        "#8AB4FF",
        "#B090FF",
        "#DC8FD4",
    ))
    PAUSE_RANGE: ClassVar[tuple[float, float]] = (0.5, 1.5)
    TRANSITION_RANGE: ClassVar[tuple[float, float]] = (3.0, 6.0)
