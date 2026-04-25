# Routines

Long-running, per-room light behaviors driven by a tick loop.

## Sections

- [Concept](#concept)
- [The LightRoutine ABC](#the-lightroutine-abc)
- [Authoring a Routine](#authoring-a-routine)
- [Registration](#registration)
- [Lifecycle](#lifecycle)

---

## Concept

A routine is an infinite light behavior scoped to one room — daylight
cycles, breathe, rainbow, fire. Routines do not self-terminate; the user
starts and stops them explicitly. They emit only `LightOnPayload` frames;
turning lights off mid-routine is the job of an [event](./events.md).

---

## The LightRoutine ABC

Defined in `clyde/routines/types.py`:

| Member | Type | Purpose |
|--------|------|---------|
| `NAME` | `ClassVar[str]` | Stable identifier used for registration and API calls |
| `tick_interval` | `ClassVar[float]` | Seconds between `step` invocations |
| `step(now, lights)` | `async` method | Returns `dict[light_key, LightOnPayload]` for this frame |

`step` receives the current `datetime` and the list of light keys in the
room. Return only the keys you want to update — omitted lights keep
their last payload.

---

## Authoring a Routine

1. Create a new file in `clyde/routines/routine_directory/`, one class
   per file.
2. Subclass `LightRoutine`, set `NAME` and `tick_interval`, and
   implement `step`.
3. Keep frame computation pure and fast — `step` runs on the event loop
   and blocks the next tick.

Minimal example (`clyde/routines/routine_directory/breathe.py`):

```python
class Breathe(LightRoutine):
    NAME: ClassVar[str] = "breathe"
    tick_interval: ClassVar[float] = 0.1

    def __init__(self) -> None:
        self.tick = 0

    async def step(self, now: datetime, lights: list[str]) -> dict[str, LightOnPayload]:
        phase = 2 * math.pi * self.tick * TICK_INTERVAL / PERIOD_S
        brightness = int(MIN + (MAX - MIN) * (1 + math.sin(phase)) / 2)
        payload = LightOnPayload(rgb_color=COLOR, brightness=brightness, transition=TICK_INTERVAL)
        self.tick += 1
        return {light: payload for light in lights}
```

For per-light variation (e.g. rainbow), index into `lights` inside the
loop and emit a distinct payload per key.

---

## Registration

Add the new class to `clyde/routines/__init__.py`:

```python
from .routine_directory import Breathe
ROUTINES: dict[str, type[LightRoutine]] = {
    Breathe.NAME: Breathe,
    # ...
}
```

`ROUTINES` is what the `set_routine` tool/API resolves against. Without
this entry the routine is unreachable.

---

## Lifecycle

`RoomManager.run_loop` (`clyde/managers/room_manager.py`) drives the
routine:

- Calls `step` every `tick_interval` seconds.
- Applies global dim factor via `scale_payload` before sending.
- On the first tick, overrides `transition` with `HANDOFF_TRANSITION_S`
  (2.0s) for a smooth visual handoff from whatever was on screen.
- Groups identical payloads into a single `turn_on_many` call to reduce
  HA traffic.
- A dim-factor change wakes the loop early and snaps brightness with a
  short transition rather than waiting for the next natural tick.

Routines persist across [events](./events.md): when an event fires, the
routine instance is preserved (with all its accumulated state) and
resumed on completion.

---

*Last updated: v0.1.0*
