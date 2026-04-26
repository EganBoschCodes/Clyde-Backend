# Changelog - v0.1.1

## Release Date

2026-04-25

## Overview

The websocket + media player release. Clyde gains a realtime push channel
for room state, a Fire TV / Spotify control surface (MCP + HTTP), and the
operational pieces that keep the Fire TV's ADB transport healthy. Earlier
scaffolding (engine, routines, events, scheduler, auth, HTTP API) is also
captured here since this is the first published changelog after the
initial split from `Smart-Home`.

## What's New

### Realtime push (websockets)

- New `clyde/realtime/` package: `RealtimeBus` singleton, `/realtime`
  websocket endpoint, and a typed `RealtimeEvent` union
  (`RoomStateEvent`, `RoomDimEvent`).
- `RoomManager` publishes a `room_state` event whenever the active
  routine changes and a `room_dim` event whenever a room's dim factor
  changes. Frontend subscribers no longer need to poll for routine /
  dim state.
- Slow subscribers are dropped rather than blocking publishers
  (`QUEUE_MAXSIZE = 64`, drop-on-full with a warning log).

### Light state lookup

- New `light_state` MCP tool and `GET /api/lights/{light}/state` HTTP
  route that return the current `LightState` (on/off, brightness, RGB)
  for a single light.

### Media players (Fire TV + Spotify)

- MCP tools and HTTP routes for `list_media_players`,
  `media_player_state`, `media_player_transport` (play/pause/stop/next/
  previous/turn_on/turn_off), `media_player_volume`,
  `media_player_select_source`, and `media_player_play_media`.
- Spotify integration (`clyde/spotify/`): client, parsers, and a
  `spotify_search` MCP tool that resolves track / album / artist /
  playlist queries to URIs for `play_media`.
- TV volume control wired through HA's `media_player.volume_set`
  service.
- Host-side ADB keepalive (systemd timer) reconnects the Fire TV's
  ADB socket every five minutes, recovering from idle drops and
  network blips. Documented in `docs/media_players.md`.

### Authentication

- Google OAuth bearer-token middleware (`clyde/auth/`) gating all
  `/api/*` and `/mcp` routes. Includes:
  - `/authorize` and `/token` proxies for the OAuth dance.
  - In-memory `TokenCache` for verified Google id_tokens.
  - OAuth metadata endpoints for MCP client discovery.
  - Email allowlist via `ALLOWED_EMAILS`.

### Documentation

- New `docs/` tree: `README.md`, `routines.md`, `events.md`,
  `media_players.md`, plus the `changelogs/` index this file lives in.
- `frontend.md` at the repo root sketches the custom home frontend
  this API is being built for.

### Cleanup

- Legacy demo scripts (`scripts/rainbow.py`, `scripts/strobe.py`)
  removed. Their behavior is covered by the `rainbow` and `disco`
  routines in `clyde/routines/routine_directory/`.

## Already-shipped scaffolding (carried into v0.1.1)

These landed earlier in the 0.1.x line and are listed here for
completeness — they are part of what 0.1.1 ships, just not new in the
recent batch.

### Engine + room dispatch

- `Engine` singleton (`ENGINE`) with per-room `RoomManager` instances.
- `RoomManager` runs the routine tick loop, handles event preemption
  with prior-routine preserve-and-resume, and supports follow-up
  routine handoff when an event returns a `LightRoutine` instance.

### Routines (`LightRoutine` subclasses)

`away`, `breathe`, `candle`, `daylight`, `disco`, `fire`, `focus`,
`iridescent`, `lightning`, `love`, `movie`, `night_light`, `ocean`,
`party`, `police`, `rainbow`, `sunset`.

### Events (`Event` subclasses)

`alarm`, `color_wipe`, `doorbell`, `mini_party`, `notify`, `roulette`.

### Scheduler

- `clyde/scheduler/` cron-like scheduler persisting jobs to
  `schedules.json`, with MCP tools and HTTP routes for
  `add_schedule`, `list_schedules`, `remove_schedule`.

### HTTP API surface

Routes under `/api/`:

- `lights/` — `list_lights`, `light_state`.
- `rooms/` — `list_rooms`, `set_routine`, `stop_routine`, `set_dim`,
  `room_off`, `fire_event`.
- `routines/list_routines`, `events/list_events`,
  `schedules/{add,list,remove}`.
- `media_players/` — see above.
- `friends/mini_party` — public-facing trigger for the `mini_party`
  event with abuse protection.
- `status` — health probe.

### MCP tool surface

Mirrors the HTTP API: `list_lights`, `light_on`, `light_off`,
`light_state`, `list_rooms`, `room_off`, `set_dim`, `set_routine`,
`stop_routine`, `list_routines`, `list_events`, `fire_event`,
`list_schedules`, `add_schedule`, `remove_schedule`,
`list_media_players`, `media_player_state`, `media_player_transport`,
`media_player_volume`, `media_player_select_source`,
`media_player_play_media`, `spotify_search`.

## Technical Details

- New packages: `clyde/auth/`, `clyde/realtime/`, `clyde/scheduler/`,
  `clyde/spotify/`, `clyde/managers/`, `clyde/events/`,
  `clyde/routines/`, `clyde/api/`, `clyde/tools/`, `clyde/utils/`.
- `clyde/server.py` mounts FastMCP at `/mcp`, wraps the app in
  `AuthMiddleware`, and starts the scheduler + engine in its lifespan.
- `pyproject.toml` bumped `0.1.0 → 0.1.1`.
- Python 3.14, `uv`-managed; `home_assistant_lib` is a path dep on
  the sibling `Home-Assistant-Lib/`.

## Commits Included

- `45a4b7a` — Initial websockets
- `843d6d0` — Light state
- `9333c2e` — Volume on the TV
- `49ea8a1` — Media player keepalive
- `e58e59c` — Documentation
- `c5819cb` — Proper config.json
- `1b9c483` — MCP Created
- `5b78d33` — Basic Media player support
- `23e424f` — Creating iridescent
- `2c15101` — API Route refresh, and room-wide dimming
- `f0d7df4` — Some fun new events
- `1cb0155` — Sunset and ocean
- `346d23a` — Batch syncing the lights
- `02df23a` — Event lister
- `7552294` — API route for turning all lights in a room off
- `6289e77` — The new schedules functionality
- `4aa735e` — New sunrise handler, and some reorganization
- `2c3a0b0` — New abuse protection on the mini party
- `3569c9e` — Mini party route
- `842f265` — Bunch of new routines, plus events
- `dfbd705` — Strong progress
- `b62e2be` — Initial scaffolding
- `be604e6` — Clyde split from Smart-Home
