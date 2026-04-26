# Clyde-Frontend: WebSocket live state sync

This is the frontend half of a feature spanning Clyde (backend) and Clyde-Frontend. The backend half is being implemented separately — your job is the React/Next.js side. Backend assumptions and the message contract are spelled out below; treat them as fixed.

## Context

Today the frontend learns about state changes by re-running a server component (`router.refresh()` after a mutation) or by polling (`Floorplan` polls every 3s). A switch flipped in one browser, by an MCP tool, or by a schedule does not appear in other open frontends until the page refreshes.

The first concrete user-visible feature: when any caller (HTTP API, MCP tool, schedule) flips a room from on → off or off → on, every connected frontend updates its toggle within ~200ms. Same for the dim slider.

This is the foundation for richer events later (per-light color/brightness changes with transitions, drawn live on the floorplan), so the message format and the client store are designed to extend.

## What the backend will do (assume this is true)

- A new WebSocket endpoint at `/api/ws` on the Clyde backend (default `ws://localhost:8765/api/ws`).
- The endpoint requires no authentication — `/api/` is already a public prefix on the LAN.
- The backend broadcasts JSON messages to every connected client whenever room state changes, regardless of whether the change came from the HTTP API, an MCP tool, or a schedule.
- Inbound messages from the frontend are not used in this iteration. Commands stay on REST.

### Message contract

Single envelope: `{ "type": "<event_name>", ...payload }`. Concretely, in this iteration:

```jsonc
// Room turned on (or routine changed)
{ "type": "room_state", "room": "kitchen", "active_routine": "daylight" }

// Room turned off
{ "type": "room_state", "room": "kitchen", "active_routine": null }

// Dim slider committed
{ "type": "room_dim", "room": "kitchen", "factor": 0.6 }
```

The `room` field matches the existing `RoomStatus.name` returned by `GET /api/rooms` (the config key, e.g. `"kitchen"`, not a display string). Existing identifiers in `RoomControls` and `page.tsx` Just Work.

Future event types (`light_state`, etc.) will land later under the same envelope. Design for that — don't hardcode a closed union that's painful to extend.

## Goals for this PR

1. Open one WebSocket per browser tab to the Clyde backend.
2. Receive `room_state` and `room_dim` events and merge them into a client-side store.
3. `RoomControls` reads its `activeRoutine` / `dimFactor` from the live store, falling back to SSR props until the first event lands.
4. Drop `router.refresh()` from the toggle and dim paths — the websocket replaces it.
5. Reconnect with backoff if the connection drops.

## Configuration

- Add `NEXT_PUBLIC_CLYDE_WS_URL` env var (e.g. `ws://localhost:8765/api/ws`). The `NEXT_PUBLIC_` prefix is required because the WS connection is opened from the browser, not from the Next.js server.
- Document it in `.env.example` if one exists; otherwise create one.
- Do **not** try to proxy WS through `src/app/api/clyde/[...path]/route.ts`. Next.js app-router route handlers cannot upgrade WebSocket connections. The browser must connect directly.

## New files

### `src/lib/realtime/messages.ts`

TypeScript types mirroring the backend Pydantic models. Hand-mirrored — the backend is the source of truth.

```ts
export type RoomStateEvent = {
  type: 'room_state';
  room: string;
  active_routine: string | null;
};

export type RoomDimEvent = {
  type: 'room_dim';
  room: string;
  factor: number;
};

export type RealtimeEvent = RoomStateEvent | RoomDimEvent;
```

### `src/lib/realtime/RealtimeProvider.tsx`

Client component (`'use client'`) that:

- Maintains a single `WebSocket` for the lifetime of the provider (mounted once near the top of the tree — see "Layout integration" below).
- Reconnects with exponential backoff (1s → 30s cap) on close/error.
- Holds two `Map`s in state:
  - `roomState: Map<string, { active_routine: string | null }>`
  - `roomDim: Map<string, number>`
- Exposes a `RealtimeContext` value: `{ roomState, roomDim }`.
- Ignores unknown `type` values gracefully (forward-compatible with future event types).
- Closes the socket cleanly on unmount.

Implementation sketch:

```tsx
'use client';

import { createContext, useEffect, useRef, useState, type ReactNode } from 'react';
import type { RealtimeEvent } from './messages';

type RoomStateMap = Map<string, { active_routine: string | null }>;
type RoomDimMap = Map<string, number>;

export const RealtimeContext = createContext<{
  roomState: RoomStateMap;
  roomDim: RoomDimMap;
}>({ roomState: new Map(), roomDim: new Map() });

const INITIAL_BACKOFF_MS = 1000;
const MAX_BACKOFF_MS = 30000;

export default function RealtimeProvider({ children }: { children: ReactNode }) {
  const [roomState, setRoomState] = useState<RoomStateMap>(new Map());
  const [roomDim, setRoomDim] = useState<RoomDimMap>(new Map());
  const wsRef = useRef<WebSocket | null>(null);
  const backoffRef = useRef(INITIAL_BACKOFF_MS);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cancelled = useRef(false);

  useEffect(() => {
    cancelled.current = false;
    const url = process.env.NEXT_PUBLIC_CLYDE_WS_URL;
    if (!url) {
      console.warn('NEXT_PUBLIC_CLYDE_WS_URL not set — realtime disabled');
      return;
    }

    function connect() {
      if (cancelled.current) return;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        backoffRef.current = INITIAL_BACKOFF_MS;
      };

      ws.onmessage = (e) => {
        let evt: RealtimeEvent;
        try {
          evt = JSON.parse(e.data) as RealtimeEvent;
        } catch {
          return;
        }
        if (evt.type === 'room_state') {
          setRoomState((prev) => {
            const next = new Map(prev);
            next.set(evt.room, { active_routine: evt.active_routine });
            return next;
          });
        } else if (evt.type === 'room_dim') {
          setRoomDim((prev) => {
            const next = new Map(prev);
            next.set(evt.room, evt.factor);
            return next;
          });
        }
      };

      ws.onclose = () => {
        wsRef.current = null;
        if (cancelled.current) return;
        const delay = backoffRef.current;
        backoffRef.current = Math.min(delay * 2, MAX_BACKOFF_MS);
        reconnectTimer.current = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      cancelled.current = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, []);

  return (
    <RealtimeContext.Provider value={{ roomState, roomDim }}>
      {children}
    </RealtimeContext.Provider>
  );
}
```

Notes:

- New `Map` per update so React notices the change (Map identity is the dependency signal).
- The unknown-event branch is intentionally silent so adding `light_state` later doesn't crash existing clients.
- Connection logic runs once per mount; `useEffect` deps are `[]` because the URL is read from a build-time env var.

### `src/lib/realtime/useRoomLive.ts`

Hook returning live overrides for a given room key. `undefined` = no event received yet, fall back to SSR data. `null` is a real value for `activeRoutine` (means off).

```ts
'use client';

import { useContext } from 'react';
import { RealtimeContext } from './RealtimeProvider';

export function useRoomLive(room: string): {
  activeRoutine: string | null | undefined;
  dimFactor: number | undefined;
} {
  const { roomState, roomDim } = useContext(RealtimeContext);
  const state = roomState.get(room);
  return {
    activeRoutine: state ? state.active_routine : undefined,
    dimFactor: roomDim.get(room),
  };
}
```

## Layout integration

In `src/app/layout.tsx`, wrap `children` with `<RealtimeProvider>` inside the existing styled-components registry so styled-components SSR continues to work:

```tsx
<StyledRegistry>
  <RealtimeProvider>{children}</RealtimeProvider>
</StyledRegistry>
```

`RealtimeProvider` is a client component; it sits below the server root layout without making the layout itself client.

## Component changes

### `src/app/_components/RoomControls/index.tsx`

Currently this component:

- Takes `activeRoutine` and `dimFactor` as props from SSR.
- Mirrors them into local state (`optimisticOn`, `dim`) and reverts on error.
- Calls `router.refresh()` after every successful mutation.

Changes:

1. Read live overrides via `useRoomLive(room)`.
2. Compute "effective" state with override-then-prop precedence:

   ```tsx
   const live = useRoomLive(room);
   const effectiveRoutine =
     live.activeRoutine !== undefined ? live.activeRoutine : activeRoutine;
   const effectiveDim = live.dimFactor !== undefined ? live.dimFactor : dimFactor;
   const isOn = effectiveRoutine !== null;
   ```

3. Update the existing `useEffect` (around line 89) so `optimisticOn` re-syncs to `isOn` whenever `effectiveRoutine` changes (not just when the prop changes). This is what makes a remote toggle visually flip the switch.

4. **Remove** the three `router.refresh()` calls (currently around lines 111, 125, 137 in `applyRoutine`, `turnOff`, `commitDim`). The WebSocket now drives the resync, and `router.refresh()` would cause an unnecessary server re-render.

5. Keep the optimistic-update + revert-on-error logic exactly as it is — it covers the 0–~200ms gap before the WS broadcast lands. Revert paths still set `optimisticOn` back to `isOn` (now `effectiveRoutine !== null`).

6. For the dim slider: on receiving a `room_dim` event for this room, update `dim` state — but only if `pending !== 'dim'`, so a remote update doesn't fight the user's in-progress drag. Concretely, add a `useEffect` that watches `effectiveDim`:

   ```tsx
   useEffect(() => {
     if (pending !== 'dim') setDim(effectiveDim);
   }, [effectiveDim, pending]);
   ```

   Initial `useState<number>(dimFactor)` stays as-is for SSR.

### `src/app/_components/Floorplan/index.tsx`

**Out of scope for this PR** — keep the 3s polling. Add a one-line TODO comment near `POLL_INTERVAL_MS` pointing at the future `light_state` event type. No other changes.

## Identifier alignment (sanity check)

- The frontend already keys rooms by `room.name` (the field returned by `GET /api/rooms`), passed through to `RoomControls` as the `room` prop.
- The backend will emit the same string in the `room` field of websocket events.
- No translation needed. If you see mismatches during testing (e.g. backend emits `"kitchen"` but frontend stored `"Kitchen"`), flag it back to the user — that means the backend implementation diverged from this contract.

## Files modified / added

- **NEW** `src/lib/realtime/messages.ts`
- **NEW** `src/lib/realtime/RealtimeProvider.tsx`
- **NEW** `src/lib/realtime/useRoomLive.ts`
- **EDIT** `src/app/layout.tsx` — wrap children in `<RealtimeProvider>` inside `<StyledRegistry>`.
- **EDIT** `src/app/_components/RoomControls/index.tsx` — consume `useRoomLive`, drop `router.refresh()`, sync `dim` from live.
- **EDIT** `.env.example` (create if missing) — document `NEXT_PUBLIC_CLYDE_WS_URL`.

## Verification

1. Set up env: in Clyde-Frontend, `echo 'NEXT_PUBLIC_CLYDE_WS_URL=ws://localhost:8765/api/ws' >> .env.local` (or run with the var inline).
2. Backend running: ask the user to start it (`uv run uvicorn clyde.server:app --host 0.0.0.0 --port 8765 --reload` from Clyde).
3. Frontend: `npm run dev`.
4. Open two browser windows on `http://localhost:3000`.
5. **Toggle test:** click the kitchen toggle in window A → window B's kitchen toggle flips within ~200ms without a page reload.
6. **Dim test:** drag the dim slider in window A → after the 200ms debounce, window B's slider tracks (and does not fight A's drag if A is still dragging).
7. **Reconnect test:** stop the backend; the frontend WS will close. Restart the backend; within a few seconds the frontends reconnect and the next mutation propagates.
8. **MCP-driven update:** ask the user to fire an MCP tool (`set_routine` / `room_off`) — both browser windows should reflect the change live.

If any of these fail, **do not** silently route around it (e.g. by re-introducing `router.refresh()`). Report the symptom so the backend half can be fixed.

## Out of scope (named so they don't sneak in)

- Per-light state events / replacing the floorplan polling.
- Inbound websocket messages from frontend → backend.
- Multi-instance / multi-host fanout — single backend process, in-memory bus.
- WebSocket auth — implicit on the LAN today, will be revisited if exposed remotely.
