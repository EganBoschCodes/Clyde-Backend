import asyncio
from datetime import datetime

from home_assistant_lib import Light, LightOffPayload, LightOnPayload, LightState, turn_off_many, turn_on_many

import clyde.utils as utils

from clyde.events.types import Event, EventContext
from clyde.realtime import BUS, LightOffEvent, LightOnEvent, LightPinEvent, RoomDimEvent, RoomEventEvent, RoomStateEvent
from clyde.routines.custom import PREVIEW_KEY
from clyde.routines.types import LightRoutine
from clyde.state import STATE, Pin


HANDOFF_TRANSITION_S = 2.0
DEFAULT_OFF_TRANSITION_S = 1.0
EVENT_RESTORE_TRANSITION_S = 0.3
DIM_SNAP_TRANSITION_S = 0.5
REJOIN_TRANSITION_S = 1.0
PIN_RESTORE_TRANSITION_S = 0.3
DEFAULT_PIN_COLOR: tuple[int, int, int] = (255, 214, 170)
DEFAULT_PIN_BRIGHTNESS = 255
MAX_CHANNEL = 255
MIN_BRIGHTNESS = 1


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
        self.pins: dict[str, Pin] = {}
        self.rejoining: set[str] = set()
        self.snap_requested = False
        self.rejoin_requested = False

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
            self.snap_requested = True
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

    def unpinned_keys(self) -> list[str]:
        return [key for key in self.lights if key not in self.pins]

    def persist_pins(self) -> None:
        _, error = STATE.set_room_pins(self.room_key, self.pins)
        if error:
            print(f"[room_manager] persist pins in '{self.room_key}' failed: {error}")

    def publish_pin(self, light_key: str, pin: Pin | None) -> None:
        BUS.publish(LightPinEvent(room=self.room_key, light=light_key, pin=pin))

    def clear_pins(self) -> None:
        if not self.pins:
            return
        released = list(self.pins.keys())
        self.pins = {}
        self.persist_pins()
        for key in released:
            self.last_payloads.pop(key, None)
            self.publish_pin(key, None)

    async def send_pin(self, light_key: str, pin: Pin, transition: float | None) -> utils.Result[None]:
        light = self.lights.get(light_key)
        if light is None:
            return utils.err(KeyError(f"Light '{light_key}' not in room '{self.room_name}'"))
        if not pin.on:
            _, error = await light.off(LightOffPayload(transition=transition))
            if error:
                return utils.err(error, f"turn_off {light.entity_id}")
            BUS.publish(LightOffEvent(room=self.room_key, light=light_key, transition=transition))
            return utils.ok(None)
        payload = LightOnPayload(rgb_color=pin.rgb_color, brightness=pin.brightness, transition=transition)
        _, error = await light.on(payload)
        if error:
            return utils.err(error, f"turn_on {light.entity_id}")
        self.publish_light_on(light_key, payload)
        return utils.ok(None)

    async def reapply_pins(self) -> None:
        for key, pin in list(self.pins.items()):
            if self.event_superseded:
                return
            _, error = await self.send_pin(key, pin, PIN_RESTORE_TRANSITION_S)
            if error:
                print(f"[room_manager] reapply pin '{key}' in '{self.room_key}' failed: {error}")

    async def restore_pins(self, pins: dict[str, Pin]) -> None:
        self.pins = {key: pin for key, pin in pins.items() if key in self.lights}
        self.persist_pins()
        for key, pin in self.pins.items():
            self.publish_pin(key, pin)
        await self.reapply_pins()

    async def resolve_pin_on(self, light_key: str, light: Light, rgb_color: tuple[int, int, int] | None, brightness: int | None) -> Pin:
        if rgb_color is not None and brightness is not None:
            return Pin(on=True, rgb_color=rgb_color, brightness=brightness)
        existing = self.pins.get(light_key)
        if existing is not None and existing.on:
            base_rgb, base_brightness = existing.rgb_color, existing.brightness
        else:
            state, error = await light.get_state()
            readable = error is None and state is not None and state.on
            base_rgb = state.rgb_color if readable and state is not None else None
            base_brightness = state.brightness if readable and state is not None else None
        return Pin(
            on=True,
            rgb_color=rgb_color or base_rgb or DEFAULT_PIN_COLOR,
            brightness=brightness if brightness is not None else (base_brightness or DEFAULT_PIN_BRIGHTNESS),
        )

    async def pin_light(self, light_key: str, on: bool, rgb_color: tuple[int, int, int] | None = None, brightness: int | None = None, transition: float | None = None) -> utils.Result[Pin]:
        light = self.lights.get(light_key)
        if light is None:
            return utils.err(KeyError(f"Light '{light_key}' not in room '{self.room_name}'"))
        if rgb_color is not None and any(c < 0 or c > MAX_CHANNEL for c in rgb_color):
            return utils.err(ValueError(f"rgb_color channels must be in [0, {MAX_CHANNEL}], got {rgb_color}"))
        if brightness is not None and (brightness < MIN_BRIGHTNESS or brightness > MAX_CHANNEL):
            return utils.err(ValueError(f"brightness must be in [{MIN_BRIGHTNESS}, {MAX_CHANNEL}], got {brightness}"))

        if on:
            pin = await self.resolve_pin_on(light_key, light, rgb_color, brightness)
        else:
            pin = Pin(on=False)
            transition = DEFAULT_OFF_TRANSITION_S if transition is None else transition

        # Pin before sending so the routine loop stops emitting for this light immediately
        previous = self.pins.get(light_key)
        self.pins[light_key] = pin
        self.last_payloads.pop(light_key, None)
        self.rejoining.discard(light_key)
        _, error = await self.send_pin(light_key, pin, transition)
        if error:
            if previous is None:
                self.pins.pop(light_key, None)
            else:
                self.pins[light_key] = previous
            return utils.err(error, f"pin {light_key}")
        self.persist_pins()
        self.publish_pin(light_key, pin)
        return utils.ok(pin)

    async def release_pin(self, light_key: str) -> utils.Result[bool]:
        if light_key not in self.lights:
            return utils.err(KeyError(f"Light '{light_key}' not in room '{self.room_name}'"))
        if self.pins.pop(light_key, None) is None:
            return utils.ok(False)
        self.persist_pins()
        self.publish_pin(light_key, None)
        if self.is_running():
            self.rejoining.add(light_key)
            self.rejoin_requested = True
            self.wake.set()
        return utils.ok(True)

    async def start(self, routine: LightRoutine) -> utils.Result[None]:
        await self.supersede_event()
        await self.cancel_active()
        self.clear_pins()
        self.active = routine
        self.last_payloads = {}
        self.rejoining = set()
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
        self.clear_pins()
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
            await self.reapply_pins()
        else:
            await self.restore_after_event(prior_routine, prior_states)
        return utils.ok(None)

    async def restore_after_event(self, prior_routine: LightRoutine | None, prior_states: dict[str, LightState]) -> None:
        if prior_routine is not None:
            self.active = prior_routine
            self.task = asyncio.create_task(self.run_loop(prior_routine))
            BUS.publish(RoomStateEvent(room=self.room_key, active_routine=prior_routine.NAME))
        else:
            for key, state in prior_states.items():
                if self.event_superseded:
                    return
                if key in self.pins:
                    continue
                await self.lights[key].restore(state, EVENT_RESTORE_TRANSITION_S)
        await self.reapply_pins()

    async def apply_off_all(self, transition: float = DEFAULT_OFF_TRANSITION_S) -> utils.Result[dict[str, str]]:
        await self.supersede_event()
        await self.cancel_active()
        self.clear_pins()
        payload = LightOffPayload(transition=transition)
        entity_ids = [light.entity_id for light in self.lights.values()]
        _, error = await turn_off_many(entity_ids, payload)
        if error:
            failed = {key: str(error) for key in self.lights.keys()}
            return utils.ok(failed)
        for key in self.lights.keys():
            BUS.publish(LightOffEvent(room=self.room_key, light=key, transition=transition))
        BUS.publish(RoomStateEvent(room=self.room_key, active_routine=None))
        return utils.ok({})

    async def run_loop(self, routine: LightRoutine) -> None:
        loop = asyncio.get_running_loop()
        next_tick = loop.time()
        first = True
        snap = False
        rejoin = False
        self.wake.clear()
        self.snap_requested = False
        self.rejoin_requested = False
        while True:
            # Pins can change between ticks, so the unpinned set is recomputed every tick
            light_keys = self.unpinned_keys()
            frame: dict[str, LightOnPayload] = {}
            if snap:
                for key in light_keys:
                    prior = self.last_payloads.get(key)
                    if prior is None or prior.brightness is None:
                        continue
                    frame[key] = LightOnPayload(brightness=prior.brightness, transition=DIM_SNAP_TRANSITION_S)
            if not snap or rejoin:
                stepped = await routine.step(datetime.now(), light_keys)
                for key, payload in stepped.items():
                    if key in self.pins:
                        continue
                    self.last_payloads[key] = payload
                    frame[key] = payload
            groups: dict[str, tuple[LightOnPayload, list[str]]] = {}
            emitted: list[tuple[str, LightOnPayload]] = []
            for key, payload in frame.items():
                light = self.lights.get(key)
                if light is None or key in self.pins:
                    continue
                outgoing = self.scale_payload(payload)
                if first:
                    outgoing = outgoing.model_copy(update={"transition": HANDOFF_TRANSITION_S})
                elif key in self.rejoining:
                    outgoing = outgoing.model_copy(update={"transition": REJOIN_TRANSITION_S})
                emitted.append((key, outgoing))
                group_key = outgoing.model_dump_json()
                existing = groups.get(group_key)
                if existing is None:
                    groups[group_key] = (outgoing, [light.entity_id])
                    continue
                existing[1].append(light.entity_id)
            self.rejoining.difference_update(frame.keys())
            await asyncio.gather(*(turn_on_many(entity_ids, grouped_payload) for grouped_payload, entity_ids in groups.values()))
            for key, outgoing in emitted:
                if key in self.pins:
                    continue
                self.publish_light_on(key, outgoing)
            first = False
            snap = False
            rejoin = False
            next_tick += routine.tick_interval
            sleep_for = next_tick - loop.time()
            if sleep_for > 0:
                try:
                    await asyncio.wait_for(self.wake.wait(), timeout=sleep_for)
                    self.wake.clear()
                    next_tick = loop.time()
                    snap = self.snap_requested
                    rejoin = self.rejoin_requested
                    self.snap_requested = False
                    self.rejoin_requested = False
                except TimeoutError:
                    pass
                continue
            next_tick = loop.time()
