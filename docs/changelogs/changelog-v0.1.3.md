# Changelog - v0.1.3

## Release Date

2026-04-26

## Overview

The palette release. Routines pick up two shared base classes
(`TransitionalPaletteRoutine` and `JitterRoutine`) that absorb the
boilerplate that had been copy-pasted across roughly half the routine
directory, and every hard-coded RGB tuple in the codebase moves to hex
literals via a new `clyde.utils.colors` helper. Two new
palette-driven routines ship (`forest`, `spring`) and four older
ones are retired (`away`, `breathe`, `night_light`, `rainbow`).

## Breaking Changes

### Routines removed: `away`, `breathe`, `night_light`, `rainbow`

These four `LightRoutine` subclasses are gone from
`clyde/routines/routine_directory/` and from the `ROUTINES` registry.

- **Persisted state.** A `state.json` carried over from v0.1.2 that
  records one of these as a room's `active_routine` will be logged and
  skipped by `Engine.restore()` (the unknown-routine path added in
  v0.1.2), so the room comes up with no routine running rather than
  crashing. If you want a room to come back up on something, set a new
  routine before upgrading or via the API after start.
- **Schedules.** Any `ScheduledEvent` whose follow-up is one of the
  removed names will fail to start the routine on fire. Edit those
  schedules to point at a current routine name.
- **MCP / API callers.** `set_routine` calls naming a removed routine
  return an error from the registry lookup. Frontends that surface a
  routine picker should drop these names from their list.

### Color tuples in events / routines moved to hex helpers

Internal-only, but worth flagging for anyone with out-of-tree
`Event` / `LightRoutine` subclasses: the tuple-literal RGB constants
in events (`alarm`, `color_wipe`, `doorbell`, `notify`, `roulette`)
and routines have been replaced with `hex_to_rgb("#…")` calls from
the new `clyde.utils` module. The old `home_assistant_lib.hue_to_rgb`
re-export is no longer used by any in-tree code (`party` now imports
`hue_to_rgb` from `clyde.utils`); existing imports against the lib
still work but the canonical location for color helpers is now
`clyde.utils`.

## What's New

### Two new routines

- **`forest`** — slow drift across a green-leaning palette
  (forest greens through olive). 0.25 s tick, 3–6 s transitions,
  0.5–1.5 s pauses.
- **`spring`** — slow drift across a pastel rainbow palette (pinks,
  peaches, yellows, mints, blues, lavenders). Same cadence as
  `forest`.

Both register through `clyde/routines/__init__.py::ROUTINES` and are
selectable via `set_routine` like any other routine.

### Shared base classes for routines

Two new base classes in `clyde/routines/` replace duplicated bodies:

- **`TransitionalPaletteRoutine`** (`transitional_palette.py`). A
  light picks a color from `PALETTE`, transitions over a random time
  in `TRANSITION_RANGE`, holds for a random time in `PAUSE_RANGE`,
  then picks again. Subclasses just declare the four `ClassVar`s
  (`PALETTE`, `PAUSE_RANGE`, `TRANSITION_RANGE`, optional
  `BRIGHTNESS`) plus `NAME` and `tick_interval`. Adopted by `disco`,
  `forest`, `love`, `ocean`, `party`, `spring`, and `sunset`.
- **`JitterRoutine`** (`jitter.py`). Per-tick pick a base color from
  `BASES`, perturb each channel by `±JITTER`, randomize brightness
  inside `BRIGHTNESS_RANGE`. Adopted by `candle` and `fire`.

The user-visible behavior of the migrated routines is roughly the
same, with one intentional change called out below.

### Palette-wide "no duplicate colors in a room" rule

`TransitionalPaletteRoutine` excludes every color currently held by
*another* light in the room when picking a new one for a given light,
falling back to "anything but my own prior color" only if the palette
is too small to satisfy the room-wide constraint. The pre-refactor
`disco` / `ocean` / `love` / `sunset` only avoided each light's own
prior color, so rooms with multiple bulbs occasionally landed on
matching colors. After v0.1.3 those routines spread across the
palette more reliably for any palette larger than the bulb count.

### `clyde.utils` color helpers

New module `clyde/utils/colors.py`, re-exported from
`clyde/utils/__init__.py`:

- `hex_to_rgb("#RRGGBB") -> RGB`
- `hue_to_rgb(hue, saturation=1.0, value=1.0) -> RGB`

Every palette and color constant in routines and events is now
expressed as a hex string converted at import time, which makes the
palettes legible in a diff and easy to paste in/out of design tools.

### Routine palette tuning

Several palettes were adjusted alongside the refactor to take
advantage of the new "no duplicate in room" rule and the hex-literal
form. The biggest visible change is `love` and `sunset`: they no
longer use a "neighbor radius + occasional anchor hold" wander, since
that mode isn't expressible in `TransitionalPaletteRoutine`. They
now drift across their full palette like the other transitional
routines, which means longer color jumps between picks but keeps the
gradient intact.

## Technical Details

- New: `clyde/routines/transitional_palette.py` — 53 lines, owns the
  drift loop that used to live in five separate routines.
- New: `clyde/routines/jitter.py` — owns the per-channel jitter loop
  for fire/candle-style routines.
- New: `clyde/utils/colors.py` plus `clyde/utils/__init__.py`
  re-export of `hex_to_rgb` and `hue_to_rgb`.
- New: `clyde/routines/routine_directory/forest.py`,
  `clyde/routines/routine_directory/spring.py`.
- Removed: `clyde/routines/routine_directory/{away,breathe,night_light,rainbow}.py`.
- `clyde/routines/routine_directory/{candle,disco,fire,love,ocean,party,sunset}.py`
  collapsed to ~25-line subclasses of the new bases. `daylight`,
  `focus`, `lightning`, `movie`, and `police` keep their bespoke
  shapes but switched their RGB literals to `hex_to_rgb`.
- Events (`alarm`, `color_wipe`, `doorbell`, `notify`, `roulette`)
  switched their color constants to `hex_to_rgb` with no behavioral
  change.
- `pyproject.toml` bumped `0.1.2 → 0.1.3`.
- Net diff: roughly +286 / −504 lines across the routines layer.

## Commits Included

- `7416704` — New transitional palette
- `ba748a8` — Jitter helper, and also working on improving some of the palette selections
- `3723c2d` — New forest routine
- `38f3883` — Spring
