# Routines

Long-running, per-room light behaviors driven by a tick loop.

## Sections

- [Concept](#concept)
- [The LightRoutine ABC](#the-lightroutine-abc)
- [Authoring a Routine](#authoring-a-routine)
- [Registration](#registration)
- [Custom Routines (Studio)](#custom-routines-studio)
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

`step` receives the current `datetime` and the list of **unpinned** light
keys in the room (see [Light Pinning](#light-pinning)). Return only the
keys you want to update — omitted lights keep their last payload.

The list can change between ticks (lights are pinned and released while
the routine runs) and can be empty. Routines must tolerate both: never
index into `lights` without a guard, and keep per-light state keyed by
light key rather than by position.

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

## Layered Routines

A routine can build on a base class and layer behavior on top of it.
`halloween` extends `TransitionalPaletteRoutine` (pumpkin oranges, witchy
purples, an occasional slime green) and adds two overlays: a per-lamp
"ghost passing" (dim, rapid flicker, sometimes an eerie green flash, then a
fade back to the palette) and a rare room-wide cold violet-white
"lightning" flicker. Overlay sequences are queued per tick; a light that
is mid-ghost has its drift payloads dropped until it recovers.

---

## Custom Routines (Studio)

Users can define their own routines without writing code. A
`CustomRoutineSpec` (`clyde/routines/custom/types.py`) has a display
`name` (1-40 chars), 1-8 `#RRGGBB` `colors`, a `style`, a `speed` in
[0, 1] (0 slowest, 1 fastest) and a `brightness` in [1, 255]. Specs are
stored in `state.json` under `custom_routines`, keyed by `studio_` plus a
slug of the name (`Spooky Night` becomes `studio_spooky_night`); an
existing key can be passed to edit a routine under a stable key.

| Style | Behavior |
|-------|----------|
| `drift` | Smooth palette crossfades across lights (`TransitionalPaletteRoutine`) |
| `flicker` | Candle/fire-like jitter around the colors (`JitterRoutine`) |
| `pulse` | The whole room breathes while slowly cycling colors |
| `chase` | Colors step light-to-light around the room in order |
| `static` | Colors distributed across lights, set once and re-sent periodically |

`clyde/routines/custom/factory.py::build_custom_routine(key, spec)` builds
a `LightRoutine` whose `NAME` is the key. `resolve_routine(name)` in
`clyde/routines/resolve.py` is the single place a routine name becomes an
instance: it checks built-in `ROUTINES`, then stored custom specs.
Saving a routine that is running restarts it with the new spec; deleting
one stops it. The reserved key `studio_preview` is used for unsaved live
previews and is never persisted as a room's active routine.

HTTP: `GET /api/studio/routines`, `PUT /api/studio/routines`,
`DELETE /api/studio/routines/{key}`, `POST /api/studio/preview`. MCP:
`list_custom_routines`, `save_custom_routine`, `delete_custom_routine`.

---

## Light Pinning

Touching a single light (`light_on` / `light_off` over MCP, or
`PUT /api/lights/{light}` over HTTP) **pins** it: the light leaves the
room's routine and holds the manual state while the routine keeps
animating the other lights.

- A pin is `{on, rgb_color, brightness}`. Omitted color/brightness keep
  the light's current values (warm white at full brightness if unknown).
- Pinned lights are excluded from `step` and never receive routine
  frames. The room dim factor does not scale them (pinned brightness is
  absolute).
- `release_light` / `DELETE /api/lights/{light}/pin` releases a pin. With
  an active routine the light rejoins on the next tick with a short
  (~1s) transition; with no routine it simply stays as it is.
- Room-level actions win: starting a routine, stopping it, or turning the
  room off clears every pin in that room.
- [Events](./events.md) still act on all lights; pins are re-applied when
  the event ends.
- Pins are persisted per room in `state.json` and re-applied on restart.

HTTP:

| Route | Body | Response |
|-------|------|----------|
| `GET /api/lights` | | each light: `{name, entity_id, room, pin}` (`pin` is null when unpinned) |
| `PUT /api/lights/{light}` | `{on, rgb_color?, brightness? (1-255), transition?}` | `{light, room, pin}` |
| `DELETE /api/lights/{light}/pin` | | `{light, room, released}` |
| `GET /api/rooms` | | each room also carries `pins: {light: pin}` |

Realtime (`/api/ws`) adds `{"type": "light_pin", room, light, pin | null}`
(on pin, update and release, including releases from room-level actions)
and `{"type": "light_off", room, light, transition | null}` (whenever a
light is turned off through the manager).

---

## Lifecycle

`RoomManager.run_loop` (`clyde/managers/room_manager.py`) drives the
routine:

- Calls `step` every `tick_interval` seconds with the currently
  unpinned lights (recomputed each tick).
- Applies global dim factor via `scale_payload` before sending.
- On the first tick, overrides `transition` with `HANDOFF_TRANSITION_S`
  (2.0s) for a smooth visual handoff from whatever was on screen.
- Groups identical payloads into a single `turn_on_many` call to reduce
  HA traffic.
- Releasing a pin wakes the loop so the light rejoins promptly.
- A dim-factor change wakes the loop early and snaps brightness with a
  short transition rather than waiting for the next natural tick.

Routines persist across [events](./events.md): when an event fires, the
routine instance is preserved (with all its accumulated state) and
resumed on completion.

---

*Last updated: v0.1.0*
