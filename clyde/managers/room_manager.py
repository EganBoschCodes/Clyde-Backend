import asyncio
from datetime import datetime

from home_assistant_lib import Light, LightOffPayload, LightOnPayload, LightState, turn_off_many, turn_on_many

import clyde.utils as utils

from clyde.events.types import Event, EventContext
from clyde.routines.types import LightRoutine


HANDOFF_TRANSITION_S = 2.0
DEFAULT_OFF_TRANSITION_S = 1.0
EVENT_RESTORE_TRANSITION_S = 0.3
DIM_SNAP_TRANSITION_S = 0.5


class RoomManager:
    def __init__(self, room_name: str, lights: dict[str, Light]) -> None:
        self.room_name = room_name
        self.lights = lights
        self.active: LightRoutine | None = None
        self.task: asyncio.Task[None] | None = None
        self.event_lock = asyncio.Lock()
        self.dim_factor: float = 1.0
        self.wake = asyncio.Event()
        self.last_payloads: dict[str, LightOnPayload] = {}

    def is_running(self) -> bool:
        return self.task is not None and not self.task.done()

    def set_dim_factor(self, factor: float) -> utils.Result[float]:
        if factor < 0.0 or factor > 1.0:
            return utils.err(ValueError(f"dim factor must be in [0.0, 1.0], got {factor}"))
        changed = factor != self.dim_factor
        self.dim_factor = factor
        if changed:
            self.wake.set()
        return utils.ok(factor)

    def scale_payload(self, payload: LightOnPayload) -> LightOnPayload:
        if payload.brightness is None or self.dim_factor == 1.0:
            return payload
        scaled = max(0, min(255, round(payload.brightness * self.dim_factor)))
        return payload.model_copy(update={"brightness": scaled})

    async def start(self, routine: LightRoutine) -> utils.Result[None]:
        stop_err = await self.stop()
        _, error = stop_err
        if error:
            return utils.err(error, f"stop previous routine in '{self.room_name}'")
        self.active = routine
        self.last_payloads = {}
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
        _, error = await asyncio.to_thread(light.on, self.scale_payload(payload))
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

    async def apply_off_all(self, transition: float = DEFAULT_OFF_TRANSITION_S) -> utils.Result[dict[str, str]]:
        stop_err = await self.stop()
        _, error = stop_err
        if error:
            return utils.err(error, f"stop routine before off in '{self.room_name}'")
        payload = LightOffPayload(transition=transition)
        entity_ids = [light.entity_id for light in self.lights.values()]
        _, error = await asyncio.to_thread(turn_off_many, entity_ids, payload)
        if error:
            failed = {key: str(error) for key in self.lights.keys()}
            return utils.ok(failed)
        return utils.ok({})

    async def run_loop(self, routine: LightRoutine) -> None:
        light_keys = list(self.lights.keys())
        loop = asyncio.get_running_loop()
        next_tick = loop.time()
        first = True
        snap = False
        self.wake.clear()
        while True:
            if snap:
                frame: dict[str, LightOnPayload] = {}
                for key in light_keys:
                    prior = self.last_payloads.get(key)
                    if prior is None or prior.brightness is None:
                        continue
                    frame[key] = LightOnPayload(brightness=prior.brightness, transition=DIM_SNAP_TRANSITION_S)
            else:
                now = datetime.now()
                frame = await routine.step(now, light_keys)
                for key, payload in frame.items():
                    self.last_payloads[key] = payload
            groups: dict[str, tuple[LightOnPayload, list[str]]] = {}
            for key, payload in frame.items():
                light = self.lights.get(key)
                if light is None:
                    continue
                outgoing = self.scale_payload(payload)
                if first:
                    outgoing = outgoing.model_copy(update={"transition": HANDOFF_TRANSITION_S})
                group_key = outgoing.model_dump_json()
                existing = groups.get(group_key)
                if existing is None:
                    groups[group_key] = (outgoing, [light.entity_id])
                    continue
                existing[1].append(light.entity_id)
            await asyncio.gather(*(asyncio.to_thread(turn_on_many, entity_ids, grouped_payload) for grouped_payload, entity_ids in groups.values()))
            first = False
            snap = False
            next_tick += routine.tick_interval
            sleep_for = next_tick - loop.time()
            if sleep_for > 0:
                try:
                    await asyncio.wait_for(self.wake.wait(), timeout=sleep_for)
                    self.wake.clear()
                    next_tick = loop.time()
                    snap = True
                except TimeoutError:
                    pass
                continue
            next_tick = loop.time()
