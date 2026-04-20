from .daylight import Daylight
from .engine import ENGINE, RoutineEngine
from .manager import RoomRoutineManager
from .party import Party
from .rainbow import Rainbow
from .types import LightRoutine


ROUTINES: dict[str, type[LightRoutine]] = {
    Daylight.NAME: Daylight,
    Rainbow.NAME: Rainbow,
    Party.NAME: Party,
}
