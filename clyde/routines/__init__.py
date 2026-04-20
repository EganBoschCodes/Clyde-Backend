from .routine_directory import Daylight, Party, Rainbow
from .types import LightRoutine

ROUTINES: dict[str, type[LightRoutine]] = {
    Daylight.NAME: Daylight,
    Rainbow.NAME: Rainbow,
    Party.NAME: Party,
}
