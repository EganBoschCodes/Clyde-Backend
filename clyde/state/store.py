import json
import os
import threading
from pathlib import Path

from pydantic import ValidationError

import clyde.utils as utils

from clyde.scheduler.types import ScheduledEvent

from .types import PersistedState, RoomState


STATE_PATH = Path(__file__).resolve().parents[2] / "state.json"
LEGACY_SCHEDULES_PATH = Path(__file__).resolve().parents[2] / "schedules.json"


class StateStore:
    def __init__(self) -> None:
        self.state = PersistedState()
        self.lock = threading.Lock()

    def load(self) -> utils.Result[PersistedState]:
        if STATE_PATH.exists():
            return self.load_from_state_file()
        if LEGACY_SCHEDULES_PATH.exists():
            return self.migrate_from_legacy()
        return utils.ok(self.state)

    def load_from_state_file(self) -> utils.Result[PersistedState]:
        try:
            raw = STATE_PATH.read_text()
        except OSError as e:
            return utils.err(e, f"read {STATE_PATH}")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            return utils.err(e, f"parse {STATE_PATH}")
        try:
            self.state = PersistedState.model_validate(data)
        except ValidationError as e:
            return utils.err(e, f"validate {STATE_PATH}")
        return utils.ok(self.state)

    def migrate_from_legacy(self) -> utils.Result[PersistedState]:
        try:
            raw = LEGACY_SCHEDULES_PATH.read_text()
        except OSError as e:
            return utils.err(e, f"read {LEGACY_SCHEDULES_PATH}")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            return utils.err(e, f"parse {LEGACY_SCHEDULES_PATH}")
        try:
            schedules = [ScheduledEvent.model_validate(s) for s in data]
        except ValidationError as e:
            return utils.err(e, f"validate {LEGACY_SCHEDULES_PATH}")
        self.state = PersistedState(schedules=schedules)
        _, error = self.write()
        if error:
            return utils.err(error, "persist migrated state")
        try:
            LEGACY_SCHEDULES_PATH.unlink()
        except OSError:
            pass
        return utils.ok(self.state)

    def schedules(self) -> list[ScheduledEvent]:
        return list(self.state.schedules)

    def rooms(self) -> dict[str, RoomState]:
        return dict(self.state.rooms)

    def set_schedules(self, schedules: list[ScheduledEvent]) -> utils.Result[None]:
        with self.lock:
            self.state = self.state.model_copy(update={"schedules": list(schedules)})
            return self.write()

    def set_room_routine(self, room: str, routine: str | None) -> utils.Result[None]:
        with self.lock:
            current = self.state.rooms.get(room) or RoomState()
            updated = current.model_copy(update={"active_routine": routine})
            rooms = {**self.state.rooms, room: updated}
            self.state = self.state.model_copy(update={"rooms": rooms})
            return self.write()

    def set_room_dim(self, room: str, factor: float) -> utils.Result[None]:
        with self.lock:
            current = self.state.rooms.get(room) or RoomState()
            updated = current.model_copy(update={"dim_factor": factor})
            rooms = {**self.state.rooms, room: updated}
            self.state = self.state.model_copy(update={"rooms": rooms})
            return self.write()

    def write(self) -> utils.Result[None]:
        payload = self.state.model_dump(mode="json")
        tmp = STATE_PATH.with_suffix(STATE_PATH.suffix + ".tmp")
        try:
            tmp.write_text(json.dumps(payload, indent=2) + "\n")
            os.replace(tmp, STATE_PATH)
        except OSError as e:
            return utils.err(e, f"write {STATE_PATH}")
        return utils.ok(None)


STATE = StateStore()
