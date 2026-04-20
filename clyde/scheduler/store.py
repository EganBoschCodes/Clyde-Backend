import json
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

import clyde.utils as utils

from .types import ScheduledEvent


SCHEDULES_PATH = Path(__file__).resolve().parents[2] / "schedules.json"

_ADAPTER = TypeAdapter(list[ScheduledEvent])


def load_schedules() -> utils.Result[list[ScheduledEvent]]:
    if not SCHEDULES_PATH.exists():
        return utils.ok([])
    try:
        raw = SCHEDULES_PATH.read_text()
    except OSError as e:
        return utils.err(e, f"read {SCHEDULES_PATH}")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return utils.err(e, f"parse {SCHEDULES_PATH}")
    try:
        return utils.ok(_ADAPTER.validate_python(data))
    except ValidationError as e:
        return utils.err(e, f"validate {SCHEDULES_PATH}")


def save_schedules(schedules: list[ScheduledEvent]) -> utils.Result[None]:
    payload = _ADAPTER.dump_python(schedules, mode="json")
    try:
        SCHEDULES_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    except OSError as e:
        return utils.err(e, f"write {SCHEDULES_PATH}")
    return utils.ok(None)
