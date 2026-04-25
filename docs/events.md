# Events

Transient, per-room light behaviors that preempt the active routine.

## Sections

- [Concept](#concept)
- [The Event ABC](#the-event-abc)
- [Authoring an Event](#authoring-an-event)
- [Registration](#registration)
- [Preemption and Restore](#preemption-and-restore)

---

## Concept

An event is a self-terminating behavior — notify flashes, doorbell
patterns, color wipes, alarms. Unlike [routines](./routines.md), events
drive their own timing (typically via `asyncio.sleep`), can turn lights
off mid-run, and finish on their own. When an event ends, the room
either restores its prior routine or hands off to a follow-up routine.

---

## The Event ABC

Defined in `clyde/events/types.py`:

| Member | Type | Purpose |
|--------|------|---------|
| `NAME` | `ClassVar[str]` | Stable identifier used for registration and API calls |
| `run(ctx)` | `async` method | Executes the event; returns a `LightRoutine` instance to start on completion, or `None` to restore prior state |

`EventContext` exposes `ctx.lights: dict[str, Light]` — the room's
lights keyed by name. Call `light.on(...)` / `light.off(...)` directly;
the manager does not buffer or group event output.

---

## Authoring an Event

1. Create a new file in `clyde/events/event_directory/`, one class per
   file.
2. Subclass `Event`, set `NAME`, and implement `async run(ctx)`.
3. Wrap blocking HA calls with `asyncio.to_thread` (the `light.on` /
   `light.off` methods are sync).
4. Drive timing with `asyncio.sleep` — there is no tick loop.

Minimal example (`clyde/events/event_directory/notify.py`):

```python
class Notify(Event):
    NAME: ClassVar[str] = "notify"

    async def run(self, ctx: EventContext) -> LightRoutine | None:
        on_payload = LightOnPayload(rgb_color=(255, 0, 0), brightness=255, transition=0.0)
        off_payload = LightOffPayload(transition=0.0)
        for _ in range(FLASHES):
            for light in ctx.lights.values():
                await asyncio.to_thread(light.on, on_payload)
            await asyncio.sleep(ON_DURATION)
            for light in ctx.lights.values():
                await asyncio.to_thread(light.off, off_payload)
            await asyncio.sleep(OFF_DURATION)
```

Returning `None` (the implicit `return` above) tells the manager to
restore the prior routine or pre-event light state.

To hand off to a routine instead, return an instance:

```python
async def run(self, ctx: EventContext) -> LightRoutine | None:
    # ...do the event...
    return Party()
```

---

## Registration

Add the new class to `clyde/events/__init__.py`:

```python
from .event_directory import Notify
EVENTS: dict[str, type[Event]] = {
    Notify.NAME: Notify,
    # ...
}
```

`EVENTS` is what the `fire_event` tool/API resolves against.

---

## Preemption and Restore

`RoomManager.fire_event` (`clyde/managers/room_manager.py`) coordinates
preemption:

1. **Snapshot** — if no routine is active, capture each light's current
   `LightState` so it can be restored bit-for-bit.
2. **Cancel** — stop the active routine task (the routine *instance* is
   kept in memory).
3. **Run** — `await event.run(ctx)`. Exceptions during run still trigger
   restore.
4. **Resume** — if `run` returned a `LightRoutine`, start it. Otherwise:
   - If a prior routine existed, resume it (state preserved).
   - Otherwise, restore each light's snapshotted state with a short
     transition (`EVENT_RESTORE_TRANSITION_S`, 0.3s).

`event_lock` serializes events per-room so two events cannot interleave.

---

*Last updated: v0.1.0*
