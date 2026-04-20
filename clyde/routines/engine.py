import clyde.utils as utils

from .manager import RoomRoutineManager
from .types import LightRoutine


class RoutineEngine:
    def __init__(self, config: utils.ClydeConfig) -> None:
        self.config = config
        self.managers: dict[str, RoomRoutineManager] = {}
        for room_key, room in config.rooms.items():
            room_lights = {k: config.lights[k] for k in room.lights}
            self.managers[room_key] = RoomRoutineManager(room.name, room_lights)

    def get(self, room: str) -> utils.Result[RoomRoutineManager]:
        manager = self.managers.get(room)
        if manager is None:
            return utils.err(KeyError(f"Unknown room '{room}'"))
        return utils.ok(manager)

    def find_room(self, light_key: str) -> utils.Result[str]:
        for room_key, room in self.config.rooms.items():
            if light_key in room.lights:
                return utils.ok(room_key)
        return utils.err(KeyError(f"Light '{light_key}' not in any room"))

    async def start(self, room: str, routine: LightRoutine) -> utils.Result[None]:
        manager, error = self.get(room)
        if error:
            return utils.err(error, f"start routine in '{room}'")
        return await manager.start(routine)

    async def stop(self, room: str) -> utils.Result[None]:
        manager, error = self.get(room)
        if error:
            return utils.err(error, f"stop routine in '{room}'")
        return await manager.stop()

    async def shutdown(self) -> None:
        for manager in self.managers.values():
            await manager.stop()


ENGINE = RoutineEngine(utils.CONFIG)
