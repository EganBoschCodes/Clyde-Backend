import asyncio
from datetime import datetime

from home_assistant_lib import Light, LightOffPayload, LightOnPayload, LightState

import clyde.utils as utils

from clyde.events.types import Event, EventContext
from clyde.routines.types import LightRoutine


HANDOFF_TRANSITION_S = 2.0
DEFAULT_OFF_TRANSITION_S = 1.0
EVENT_RESTORE_TRANSITION_S = 0.3


class RoomManager:
    def __init__(self, room_name: str, lights: dict[str, Light]) -> None:
        self.room_name = room_name
        self.lights = lights
        self.active: LightRoutine | None = None
        self.task: asyncio.Task[None] | None = None
        self.event_lock = asyncio.Lock()

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
        await self.cancel_task()
        self.active = None
        return utils.ok(None)

    async def cancel_task(self) -> None:
        if self.task is not None:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

    async def fire_event(self, event: Event) -> utils.Result[None]:
        async with self.event_lock:
            prior_routine = self.active
            prior_states: dict[str, LightState] = {}
            if prior_routine is None:
                for key, light in self.lights.items():
                    state, error = await asyncio.to_thread(light.get_state)
                    if error or state is None:
                        continue
                    prior_states[key] = state
            await self.cancel_task()
            try:
                follow_up = await event.run(EventContext(lights=self.lights))
            except Exception as e:
                await self.restore_after_event(prior_routine, prior_states)
                return utils.err(e, f"event '{event.NAME}' in '{self.room_name}'")
            if follow_up is not None:
                self.active = follow_up
                self.task = asyncio.create_task(self.run_loop(follow_up))
            else:
                await self.restore_after_event(prior_routine, prior_states)
            return utils.ok(None)

    async def restore_after_event(self, prior_routine: LightRoutine | None, prior_states: dict[str, LightState]) -> None:
        if prior_routine is not None:
            self.active = prior_routine
            self.task = asyncio.create_task(self.run_loop(prior_routine))
            return
        for key, state in prior_states.items():
            await asyncio.to_thread(self.lights[key].restore, state, EVENT_RESTORE_TRANSITION_S)

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
