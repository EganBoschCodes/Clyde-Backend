import asyncio
from datetime import datetime

from home_assistant_lib import Light, LightOffPayload, LightOnPayload

import clyde.utils as utils

from .types import LightRoutine


HANDOFF_TRANSITION_S = 2.0
DEFAULT_OFF_TRANSITION_S = 1.0


class RoomRoutineManager:
    def __init__(self, room_name: str, lights: dict[str, Light]) -> None:
        self.room_name = room_name
        self.lights = lights
        self.active: LightRoutine | None = None
        self.task: asyncio.Task[None] | None = None

    def is_running(self) -> bool:
        return self.task is not None and not self.task.done()

    async def start(self, routine: LightRoutine) -> utils.Result[None]:
        stop_err = await self.stop()
        _, error = stop_err
        if error:
            return utils.err(error, f"stop previous routine in '{self.room_name}'")
        self.active = routine
        self.task = asyncio.create_task(self.run_loop(routine))
        return utils.ok(None)

    async def stop(self) -> utils.Result[None]:
        if self.task is not None:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        self.active = None
        return utils.ok(None)

    async def apply_on(self, light_key: str, payload: LightOnPayload) -> utils.Result[None]:
        stop_err = await self.stop()
        _, error = stop_err
        if error:
            return utils.err(error, f"stop routine before manual on in '{self.room_name}'")
        light = self.lights.get(light_key)
        if light is None:
            return utils.err(KeyError(f"Light '{light_key}' not in room '{self.room_name}'"))
        _, error = await asyncio.to_thread(light.on, payload)
        if error:
            return utils.err(error, f"turn_on {light.entity_id}")
        return utils.ok(None)

    async def apply_off(self, light_key: str, transition: float = DEFAULT_OFF_TRANSITION_S) -> utils.Result[None]:
        stop_err = await self.stop()
        _, error = stop_err
        if error:
            return utils.err(error, f"stop routine before off in '{self.room_name}'")
        light = self.lights.get(light_key)
        if light is None:
            return utils.err(KeyError(f"Light '{light_key}' not in room '{self.room_name}'"))
        payload = LightOffPayload(transition=transition)
        _, error = await asyncio.to_thread(light.off, payload)
        if error:
            return utils.err(error, f"turn_off {light.entity_id}")
        return utils.ok(None)

    async def run_loop(self, routine: LightRoutine) -> None:
        light_keys = list(self.lights.keys())
        first = True
        while True:
            now = datetime.now()
            frame = await routine.step(now, light_keys)
            for key, payload in frame.items():
                light = self.lights.get(key)
                if light is None:
                    continue
                outgoing = payload
                if first:
                    outgoing = payload.model_copy(update={"transition": HANDOFF_TRANSITION_S})
                await asyncio.to_thread(light.on, outgoing)
            first = False
            await asyncio.sleep(routine.tick_interval)
