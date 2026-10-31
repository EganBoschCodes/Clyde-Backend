import asyncio
from datetime import datetime

from home_assistant_lib import Light, LightOffPayload, LightOnPayload, LightState, turn_off_many, turn_on_many

import clyde.utils as utils

from clyde.events.types import Event, EventContext
from clyde.realtime import BUS, LightOnEvent, RoomDimEvent, RoomEventEvent, RoomStateEvent
from clyde.routines.custom import PREVIEW_KEY
from clyde.routines.types import LightRoutine
from clyde.state import STATE


HANDOFF_TRANSITION_S = 2.0
DEFAULT_OFF_TRANSITION_S = 1.0
EVENT_RESTORE_TRANSITION_S = 0.3
DIM_SNAP_TRANSITION_S = 0.5


class RoomManager:
    def __init__(self, room_key: str, room_name: str, lights: dict[str, Light]) -> None:
        self.room_key = room_key
        self.room_name = room_name
        self.lights = lights
        self.active: LightRoutine | None = None
        self.task: asyncio.Task[None] | None = None
        self.event_lock = asyncio.Lock()
        self.event_task: asyncio.Task[LightRoutine | None] | None = None
        self.active_event: Event | None = None
        self.event_done: asyncio.Future[None] | None = None
        self.event_cancel_requested = False
        self.event_superseded = False
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
            _, error = STATE.set_room_dim(self.room_key, factor)
            if error:
                print(f"[room_manager] persist dim in '{self.room_key}' failed: {error}")
            self.wake.set()
            BUS.publish(RoomDimEvent(room=self.room_key, factor=factor))
        return utils.ok(factor)

    def persist_active(self) -> None:
        name = self.active.NAME if self.active is not None and self.active.NAME != PREVIEW_KEY else None
        _, error = STATE.set_room_routine(self.room_key, name)
        if error:
            print(f"[room_manager] persist active in '{self.room_key}' failed: {error}")

    def scale_payload(self, payload: LightOnPayload) -> LightOnPayload:
        if payload.brightness is None or self.dim_factor == 1.0:
            return payload
        scaled = max(0, min(255, round(payload.brightness * self.dim_factor)))
        return payload.model_copy(update={"brightness": scaled})

    def publish_light_on(self, light_key: str, payload: LightOnPayload) -> None:
        BUS.publish(LightOnEvent(
            room=self.room_key,
            light=light_key,
            rgb_color=payload.rgb_color,
            brightness=payload.brightness,
            transition=payload.transition,
        ))

    async def start(self, routine: LightRoutine) -> utils.Result[None]:
        await self.supersede_event()
        await self.cancel_active()
        self.active = routine
        self.last_payloads = {}
        self.task = asyncio.create_task(self.run_loop(routine))
        self.persist_active()
        BUS.publish(RoomStateEvent(room=self.room_key, active_routine=routine.NAME))
        return utils.ok(None)

    async def cancel_active(self) -> None:
        await self.cancel_task()
        had_active = self.active is not None
        self.active = None
        if had_active:
            self.persist_active()

    async def halt(self) -> None:
        await self.supersede_event()
        await self.cancel_task()

    async def stop(self) -> utils.Result[None]:
        await self.supersede_event()
        had_active = self.active is not None
        await self.cancel_active()
        if had_active:
            BUS.publish(RoomStateEvent(room=self.room_key, active_routine=None))
        return utils.ok(None)

    async def cancel_task(self) -> None:
        if self.task is not None:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

    async def interrupt_event(self, superseded: bool) -> bool:
        done = self.event_done
        if self.active_event is None or done is None:
            return False
        already = self.event_cancel_requested or self.event_superseded
        if superseded:
            self.event_superseded = True
        else:
            self.event_cancel_requested = True
        if self.event_task is not None:
            self.event_task.cancel()
        await asyncio.shield(done)
        return not already

    async def cancel_event(self) -> utils.Result[bool]:
        cancelled = await self.interrupt_event(superseded=False)
        return utils.ok(cancelled)

    async def supersede_event(self) -> None:
        await self.interrupt_event(superseded=True)

    def begin_event(self, event: Event) -> None:
        self.active_event = event
        self.event_cancel_requested = False
        self.event_superseded = False
        self.event_done = asyncio.get_running_loop().create_future()
        BUS.publish(RoomEventEvent(room=self.room_key, active_event=event.NAME))

    def end_event(self) -> None:
        self.event_task = None
        self.active_event = None
        BUS.publish(RoomEventEvent(room=self.room_key, active_event=None))

    def finish_event(self) -> None:
        done = self.event_done
        self.event_done = None
        if done is not None and not done.done():
            done.set_result(None)

    async def fire_event(self, event: Event) -> utils.Result[None]:
        async with self.event_lock:
            self.begin_event(event)
            try:
                return await self.run_event(event)
            finally:
                self.end_event()
                self.finish_event()

    async def run_event(self, event: Event) -> utils.Result[None]:
        prior_routine = self.active
        prior_states: dict[str, LightState] = {}
        if prior_routine is None:
            for key, light in self.lights.items():
                state, error = await light.get_state()
                if error or state is None:
                    continue
                prior_states[key] = state

        # Cancelled or superseded before the event ever started
        if self.event_cancel_requested or self.event_superseded:
            return utils.ok(None)

        await self.cancel_task()
        ctx = EventContext(room_key=self.room_key, lights=self.lights, set_dim_factor=self.set_dim_factor)
        task = asyncio.create_task(event.run(ctx))
        self.event_task = task
        try:
            follow_up = await task
        except asyncio.CancelledError:
            # Distinguish cancel_event/supersede (flags) from the caller itself being cancelled
            interrupted = self.event_cancel_requested or self.event_superseded
            if not self.event_superseded:
                await self.restore_after_event(prior_routine, prior_states)
            if not interrupted:
                raise
            return utils.ok(None)
        except Exception as e:
            if not self.event_superseded:
                await self.restore_after_event(prior_routine, prior_states)
            return utils.err(e, f"event '{event.NAME}' in '{self.room_name}'")

        if self.event_superseded or self.event_cancel_requested:
            if not self.event_superseded:
                await self.restore_after_event(prior_routine, prior_states)
            return utils.ok(None)
        if follow_up is not None:
            self.active = follow_up
            self.task = asyncio.create_task(self.run_loop(follow_up))
            self.persist_active()
            BUS.publish(RoomStateEvent(room=self.room_key, active_routine=follow_up.NAME))
        else:
            await self.restore_after_event(prior_routine, prior_states)
        return utils.ok(None)

    async def restore_after_event(self, prior_routine: LightRoutine | None, prior_states: dict[str, LightState]) -> None:
        if prior_routine is not None:
            self.active = prior_routine
            self.task = asyncio.create_task(self.run_loop(prior_routine))
            BUS.publish(RoomStateEvent(room=self.room_key, active_routine=prior_routine.NAME))
            return
        for key, state in prior_states.items():
            if self.event_superseded:
                return
            await self.lights[key].restore(state, EVENT_RESTORE_TRANSITION_S)

    async def apply_on(self, light_key: str, payload: LightOnPayload) -> utils.Result[None]:
        await self.supersede_event()
        await self.cancel_active()
        light = self.lights.get(light_key)
        if light is None:
            return utils.err(KeyError(f"Light '{light_key}' not in room '{self.room_name}'"))
        outgoing = self.scale_payload(payload)
        _, error = await light.on(outgoing)
        if error:
            return utils.err(error, f"turn_on {light.entity_id}")
        self.publish_light_on(light_key, outgoing)
        return utils.ok(None)

    async def apply_off(self, light_key: str, transition: float = DEFAULT_OFF_TRANSITION_S) -> utils.Result[None]:
        await self.supersede_event()
        await self.cancel_active()
        light = self.lights.get(light_key)
        if light is None:
            return utils.err(KeyError(f"Light '{light_key}' not in room '{self.room_name}'"))
        payload = LightOffPayload(transition=transition)
        _, error = await light.off(payload)
        if error:
            return utils.err(error, f"turn_off {light.entity_id}")
        return utils.ok(None)

    async def apply_off_all(self, transition: float = DEFAULT_OFF_TRANSITION_S) -> utils.Result[dict[str, str]]:
        await self.supersede_event()
        await self.cancel_active()
        payload = LightOffPayload(transition=transition)
        entity_ids = [light.entity_id for light in self.lights.values()]
        _, error = await turn_off_many(entity_ids, payload)
        if error:
            failed = {key: str(error) for key in self.lights.keys()}
            return utils.ok(failed)
        BUS.publish(RoomStateEvent(room=self.room_key, active_routine=None))
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
            emitted: list[tuple[str, LightOnPayload]] = []
            for key, payload in frame.items():
                light = self.lights.get(key)
                if light is None:
                    continue
                outgoing = self.scale_payload(payload)
                if first:
                    outgoing = outgoing.model_copy(update={"transition": HANDOFF_TRANSITION_S})
                emitted.append((key, outgoing))
                group_key = outgoing.model_dump_json()
                existing = groups.get(group_key)
                if existing is None:
                    groups[group_key] = (outgoing, [light.entity_id])
                    continue
                existing[1].append(light.entity_id)
            await asyncio.gather(*(turn_on_many(entity_ids, grouped_payload) for grouped_payload, entity_ids in groups.values()))
            for key, outgoing in emitted:
                self.publish_light_on(key, outgoing)
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
