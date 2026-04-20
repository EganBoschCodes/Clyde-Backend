# Clyde

The MCP server and web API frontend for our local Home Assistant instance.
Two consumers, one codebase:

1. **MCP** — exposes HA tools to LLMs (lights on/off, color, brightness,
   scenes; over time: locks, sensors, scenes, routines).
2. **Web API** — HTTP routes for a custom home-assistant frontend we're
   building.

Clyde talks to HA through `home_assistant_lib`, which wraps the HA REST /
WebSocket API. Clyde does not talk to the Zigbee radio or any hardware
directly.

## Scope

- MCP tool registration + handlers.
- HTTP API routes for the frontend.
- Long-running light **routines** and transient light **events**.

## Package structure

- `clyde/routines/` — room-scoped, long-running light behaviors.
  - `types.py` — `LightRoutine` ABC (`NAME`, `tick_interval`, async
    `step(now, lights) -> dict[str, LightOnPayload]`).
  - `engine.py` — `RoutineEngine` singleton `ENGINE`, per-room dispatch.
  - `manager.py` — `RoomRoutineManager` owns one room's active routine /
    event, runs the tick loop, and handles event preemption with prior-
    routine preserve-and-resume.
  - `routine_directory/` — concrete `LightRoutine` subclasses, one per
    file. Registered by `NAME` in `clyde/routines/__init__.py::ROUTINES`.
- `clyde/events/` — room-scoped, transient behaviors that preempt the
  active routine and restore it on completion.
  - `types.py` — `Event` ABC (`NAME`, async `run(ctx: EventContext)`).
    Events drive their own timing via `ctx.lights` and return when done.
  - `event_directory/` — concrete `Event` subclasses. Registered in
    `clyde/events/__init__.py::EVENTS`.
- `clyde/tools/` — MCP tool entrypoints (one file per tool).
- `clyde/api/` — HTTP route entrypoints (one file per route).
- `scripts/` — legacy standalone demos (`rainbow.py`, `strobe.py`). Do
  **not** add new behavior here — use `routine_directory/` or
  `event_directory/`.

## Routine vs Event — when to use which

- **Routine** — long-running, infinite tick loop, no self-termination,
  can only emit `LightOnPayload`. Example: daylight color cycle, rainbow,
  breathe, fire. User starts/stops explicitly.
- **Event** — transient, self-terminating, drives its own timing. Can
  turn lights off mid-run, flash, etc. On completion the manager
  restores the prior routine instance (state preserved) and snaps lights
  back to their pre-event state if no routine was running. Example:
  notify flash, doorbell pattern, color wipe.

## Non-scope

- HA container + config — lives in sibling `Home-Assistant-Deployment/`.
- Raw HA API wrapping + Pydantic models — lives in sibling
  `Home-Assistant-Lib/` (imported as `home_assistant_lib`).

## Python style

- **Single-line function signatures.** Keep `def name(arg: T, ...) -> R:`
  on one line, even if it gets long.
- **No `__all__`.** Control visibility via what barrel files import.
- Follow the patterns documented by the `python:write-python` skill.

## Python tooling

- **`uv` is the standard.** No `pip`, `pyenv`, `venv`, or system Python.
- `home_assistant_lib` is a path dependency on sibling
  `../Home-Assistant-Lib` (see `[tool.uv.sources]` in `pyproject.toml`).
- `uv sync` to install, `uv run scripts/rainbow.py` to run a script.

## Working style for agents

- Changes to the HA-facing API surface usually belong in
  `home_assistant_lib`, not here. Push them upstream before building Clyde
  features on top.
- Ask before destructive actions on the Pi (restarting HA, editing
  automations.yaml live, etc.).
