import clyde.utils as utils

from clyde.state import STATE

from . import ROUTINES
from .custom import build_custom_routine
from .types import LightRoutine


def resolve_routine(name: str) -> utils.Result[LightRoutine]:
    klass = ROUTINES.get(name)
    if klass is not None:
        return utils.ok(klass())
    spec = STATE.custom_routines().get(name)
    if spec is None:
        return utils.err(KeyError(f"Unknown routine '{name}'"))
    return utils.ok(build_custom_routine(name, spec))
