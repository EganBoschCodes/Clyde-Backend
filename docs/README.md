# Clyde Documentation

MCP server and HTTP API frontend for a local Home Assistant instance.

## Sections

- [Overview](#overview)
- [Project Intent](#project-intent)
- [Getting Started](#getting-started)
- [Architecture](#architecture)
- [Additional Docs](#additional-docs)

---

## Overview

Clyde exposes a Home Assistant deployment to two consumers from a single
codebase: an **MCP server** for LLM tool use (lights, media players,
scenes, schedules) and an **HTTP API** for a custom home-frontend. It
talks to HA through the sibling `home_assistant_lib` wrapper — never
directly to Zigbee or hardware.

---

## Project Intent

This repo is **not** packaged to work out-of-the-box for arbitrary
deployments. It's my personal smart-home stack, built in the open. Two
audiences in mind:

- **Anyone watching the build** — the commit history and code are the
  documentation of what I'm trying and why.
- **Anyone forking** — take this as a starting point for your own
  smart-home project. Expect to rewrite `config.json`, the auth
  allowlist, and likely a chunk of the routines/events to match your
  hardware and preferences.

This is personal software and thus entirely made with Claude Code, so don't
look to this as my standard of quality code.

There is no support promise, no stable API, and no compatibility
guarantee across commits.

---

## Getting Started

```bash
uv sync
uv run uvicorn clyde.server:app --host 0.0.0.0 --port 8765
```

Required env vars (see `clyde/auth/config.py`):

| Variable | Purpose |
|----------|---------|
| `GOOGLE_CLIENT_ID` | OAuth client ID for the bearer-token flow |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret |
| `ALLOWED_EMAILS` | Comma-separated allowlist of Google account emails |

A `config.json` at the repo root defines `lights`, `rooms`, and
`media_players` — see `clyde/utils/config.py` for the schema.

---

## Architecture

| Package | Role |
|---------|------|
| `clyde/api/` | HTTP route handlers (one file per route) |
| `clyde/tools/` | MCP tool entrypoints (one file per tool) |
| `clyde/auth/` | Google OAuth bearer-token middleware + `/authorize`, `/token` proxies |
| `clyde/managers/` | `Engine` singleton + per-room dispatch for routines and events |
| `clyde/routines/` | Long-running per-room light behaviors (`LightRoutine` subclasses) |
| `clyde/events/` | Transient per-room behaviors that preempt routines (`Event` subclasses) |
| `clyde/scheduler/` | Cron-like schedules, persisted via the state store |
| `clyde/state/` | `state.json` persistence: schedules, active routine per room, dim factor per room |
| `clyde/utils/` | Config loading, HTTP client helpers, `Result` type |

`clyde/server.py` mounts the FastMCP app at `/mcp`, wraps it with
`AuthMiddleware`, and starts the scheduler + engine in its lifespan.

---

## Additional Docs

| Document | Description |
|----------|-------------|
| [routines.md](./routines.md) | Authoring long-running per-room light behaviors |
| [events.md](./events.md) | Authoring transient, preempting light behaviors |
| [media_players.md](./media_players.md) | Fire TV (ADB) integration + keepalive timer |
| [changelogs/](./changelogs/) | Version history and release notes |

---

*Last updated: v0.1.0*
