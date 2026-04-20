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
- Long-running routines (the starter set lives in `scripts/` — e.g.
  `rainbow.py`, `strobe.py`).

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
