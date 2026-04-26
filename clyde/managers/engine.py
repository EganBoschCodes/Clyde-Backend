import clyde.utils as utils

from clyde.events.types import Event
from clyde.routines import ROUTINES
from clyde.routines.types import LightRoutine
from clyde.state import STATE

from .room_manager import RoomManager


class Engine:
    def __init__(self, config: utils.ClydeConfig) -> None:
        self.config = config
        self.managers: dict[str, RoomManager] = {}
        for room_key, room in config.rooms.items():
            room_lights = {k: config.lights[k] for k in room.lights}
            self.managers[room_key] = RoomManager(room_key, room.name, room_lights)

    def get(self, room: str) -> utils.Result[RoomManager]:
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

    def set_dim_factor(self, room: str, factor: float) -> utils.Result[float]:
        manager, error = self.get(room)
        if error:
            return utils.err(error, f"set dim factor in '{room}'")
        return manager.set_dim_factor(factor)

    async def fire_event(self, room: str, event: Event) -> utils.Result[None]:
        manager, error = self.get(room)
        if error:
            return utils.err(error, f"fire event in '{room}'")
        return await manager.fire_event(event)

    async def restore(self) -> None:
        for room_key, room_state in STATE.rooms().items():
            manager = self.managers.get(room_key)
            if manager is None:
                continue
            if room_state.dim_factor != 1.0:
                manager.set_dim_factor(room_state.dim_factor)
            if room_state.active_routine is None:
                continue
            klass = ROUTINES.get(room_state.active_routine)
            if klass is None:
                print(f"[engine] unknown routine '{room_state.active_routine}' for room '{room_key}', skipping restore")
                continue
            _, error = await manager.start(klass())
            if error:
                print(f"[engine] restore '{room_state.active_routine}' in '{room_key}' failed: {error}")

    async def shutdown(self) -> None:
        for manager in self.managers.values():
            await manager.halt()


ENGINE = Engine(utils.CONFIG)
