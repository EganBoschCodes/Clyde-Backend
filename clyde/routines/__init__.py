from .engine import ENGINE
from .routine_directory import (
    Away,
    Breathe,
    Candle,
    Daylight,
    Fire,
    Focus,
    Lightning,
    Movie,
    NightLight,
    Party,
    Police,
    Rainbow,
    Sunrise,
    Sunset,
)
from .types import LightRoutine

ROUTINES: dict[str, type[LightRoutine]] = {
    Away.NAME: Away,
    Breathe.NAME: Breathe,
    Candle.NAME: Candle,
    Daylight.NAME: Daylight,
    Fire.NAME: Fire,
    Focus.NAME: Focus,
    Lightning.NAME: Lightning,
    Movie.NAME: Movie,
    NightLight.NAME: NightLight,
    Party.NAME: Party,
    Police.NAME: Police,
    Rainbow.NAME: Rainbow,
    Sunrise.NAME: Sunrise,
    Sunset.NAME: Sunset,
}
