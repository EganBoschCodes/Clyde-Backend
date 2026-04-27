from .routine_directory import (
    Candle,
    Daylight,
    Disco,
    Fire,
    Focus,
    Iridescent,
    Lightning,
    Love,
    Movie,
    Ocean,
    Party,
    Police,
    Sunset,
)
from .types import LightRoutine

ROUTINES: dict[str, type[LightRoutine]] = {
    Candle.NAME: Candle,
    Daylight.NAME: Daylight,
    Disco.NAME: Disco,
    Fire.NAME: Fire,
    Focus.NAME: Focus,
    Iridescent.NAME: Iridescent,
    Lightning.NAME: Lightning,
    Love.NAME: Love,
    Movie.NAME: Movie,
    Ocean.NAME: Ocean,
    Party.NAME: Party,
    Police.NAME: Police,
    Sunset.NAME: Sunset,
}
