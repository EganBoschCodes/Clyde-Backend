# Changelog - v0.1.2

## Release Date

2026-04-25

## Overview

The persistence + scheduling release. Clyde now survives backend restarts
with active routines, per-room dim factors, and schedules all kept in a
single `state.json`. Schedules pick up day-of-week filtering, the alarm
event forces the room back to full brightness, and the realtime bus
streams a per-light push event whenever a light changes.

## Breaking Changes

### Schedules now require `days_of_week`

`ScheduledEvent` adds a required `days_of_week: tuple[int, ...]` field
(`0 = Monday … 6 = Sunday`, must be non-empty, deduped, in range). The
MCP `add_schedule` tool and the `POST /api/schedules` body both require
it.

- **MCP / HTTP callers** must pass `days_of_week` on every new schedule.
  A schedule that previously fired daily should now pass
  `[0, 1, 2, 3, 4, 5, 6]`.
- **Existing `schedules.json` files** from v0.1.1 will fail validation
  during migration to `state.json` because the field is missing. Either
  delete `schedules.json` and recreate the schedules through the API, or
  hand-edit each entry to add `"days_of_week": [0, 1, 2, 3, 4, 5, 6]`
  before first startup on v0.1.2.

### `clyde.scheduler` re-exports trimmed

`SCHEDULER`, `Scheduler`, `SCHEDULES_PATH`, `load_schedules`, and
`save_schedules` are no longer re-exported from `clyde.scheduler`. The
file-backed schedule store (`clyde/scheduler/store.py`) has been
removed — schedules now live in the central state store. Import
`SCHEDULER` from `clyde.scheduler.scheduler` and `ScheduledEvent` from
`clyde.scheduler` (still re-exported).

## What's New

### State persistence across restarts

- New `clyde/state/` package and `StateStore` singleton (`STATE`) that
  owns a single `state.json` at the repo root. It tracks:
  - `schedules` — replaces the old `schedules.json`.
  - `rooms[room].active_routine` — the routine running in each room.
  - `rooms[room].dim_factor` — the current dim level for each room.
- `RoomManager` writes through to `STATE` whenever the active routine
  changes (start / stop / event handoff) or the dim factor changes.
- `Engine.restore()` runs in the server lifespan after
  `STATE.load()` and replays each room's persisted dim factor and
  routine, so a Pi reboot or `systemctl restart` no longer leaves rooms
  dark or stuck on a different routine. Unknown routine names are
  logged and skipped rather than crashing the boot.
- `Engine.shutdown()` now uses a new `RoomManager.halt()` that cancels
  the tick task **without** clearing `active`, so the persisted state
  reflects what should resume on next start.
- Atomic write via `os.replace` on a `.tmp` file prevents torn writes
  if the host loses power mid-save.
- One-shot migration: on first startup against an existing
  `schedules.json` (and no `state.json`), Clyde imports the schedules
  into `state.json` and deletes the legacy file.

### Day-of-week scheduling

- `ScheduledEvent.days_of_week` plus a `runs_on(weekday)` helper. The
  scheduler skips schedules whose weekday is not in the set both during
  startup catch-up and the run loop.
- MCP tool descriptions updated to document the
  `0 = Mon … 6 = Sun` convention.

### Per-light realtime push events

- New `LightOnEvent` on the realtime bus (`type: "light_on"`,
  `room`, `light`, `rgb_color`, `brightness`, `transition`).
- `RoomManager` publishes a `light_on` for every light it turns on,
  both from routine ticks (one event per scaled payload after batching)
  and from direct `apply_on` calls.
- `EventContext` gains an async `turn_on(light_key, payload)` helper
  that runs the HA call off-thread and publishes the same event, so
  events get realtime push for free without re-implementing it.
- Frontends can now reflect individual light changes without polling
  `light_state`. (The existing `room_state` and `room_dim` events are
  unchanged.)

### Alarm forces full brightness

- The `alarm` event now calls `ctx.set_dim_factor(1.0)` at the start of
  its run, guaranteeing the wake-up ramp hits full brightness even if
  the room was dimmed overnight.
- `EventContext` exposes `set_dim_factor: Callable[[float], Result[float]]`
  threaded through from the owning `RoomManager` so any event can
  override dim for the duration of its run.

### Documentation

- `docs/README.md` package map now lists `clyde/state/` and notes that
  `clyde/scheduler/` persists through the state store.
- The placeholder `frontend.md` at the repo root has been removed.

## Technical Details

- New module: `clyde/state/{__init__,store,types}.py` —
  `PersistedState`, `RoomState`, and `StateStore` with a `threading.Lock`
  guarding writes.
- Removed: `clyde/scheduler/store.py`. `Scheduler.start/add/remove`
  now read and write through `STATE.schedules()` / `STATE.set_schedules()`.
- `RoomManager` adds `persist_active()`, `halt()`, and a `LightOnEvent`
  publish helper; `set_dim_factor` is now persisted.
- `EventContext` constructor signature changed to
  `EventContext(room_key, lights, set_dim_factor)`. All in-tree events
  already use the new shape; out-of-tree event subclasses must update
  their construction site (only `RoomManager.fire_event` constructs it
  inside Clyde).
- `clyde/server.py` lifespan: `STATE.load()` → `ENGINE.restore()` →
  `SCHEDULER.start()`.
- `.gitignore` now ignores `state.json`.
- `pyproject.toml` bumped `0.1.1 → 0.1.2`.

## Commits Included

- `5ff6d3c` — Websocket events for when the lights get updated
- `d63fa51` — Alarm sets the room brightness to full on the start of the event
- `3ca9a34` — Store the days of the week in the schedules
- `31419e2` — Storing state between backend restarts
