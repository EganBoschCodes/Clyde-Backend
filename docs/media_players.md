# Media Players

Fire TV control via Home Assistant's `androidtv` integration, plus the
host-side keepalive that keeps its ADB connection healthy.

## Sections

- [Overview](#overview)
- [HA Integration](#ha-integration)
- [ADB Keepalive Timer](#adb-keepalive-timer)
- [Troubleshooting](#troubleshooting)

---

## Overview

Clyde exposes media players through MCP tools backed by HA's
`media_player.*` services. Today there is one device:

| Name | Entity | Device |
|------|--------|--------|
| `fire_tv` | `media_player.fire_tv` | Fire TV on the LAN, ADB transport |

The `media_players` block in `config.json` maps friendly names to HA
entity IDs; tool handlers live under `clyde/tools/media_player_*.py`.

---

## HA Integration

The Fire TV is registered with HA's **AndroidTV** integration in `firetv`
mode, configured with the device's LAN IP and the standard ADB port. Host
and port are stored in HA's config entry — not duplicated here.

HA uses its own ADB key at `config/.storage/androidtv_adbkey` (separate
from the host's `~/.android/adbkey`). Both keys must be authorized on the
Fire TV. The first time either key is used, the TV shows an "Allow USB
debugging?" prompt that must be accepted on-screen.

If the integration's config entry is missing entirely (entities exist but
return HTTP 404), re-add it through the HA UI under **Settings → Devices
& Services → Add Integration → Android TV**, or via the HA REST API by
opening a flow on the `androidtv` handler and submitting `host`,
`device_class=firetv`, `port`.

---

## ADB Keepalive Timer

Fire TVs drop their ADB socket after periods of inactivity, network
blips, or device sleep. A systemd timer on the host reconnects every
five minutes — a no-op when healthy, a recovery when stale.

| Unit | Path |
|------|------|
| Service | `/etc/systemd/system/firetv-adb-keepalive.service` |
| Timer | `/etc/systemd/system/firetv-adb-keepalive.timer` |

The service is a `oneshot` running `adb connect <fire-tv-ip>:<port>` as
the deploy user. The timer fires `OnBootSec=1min`, then every `5min`
(`AccuracySec=15s`, `Persistent=true`).

Useful commands:

```bash
systemctl list-timers firetv-adb-keepalive
journalctl -u firetv-adb-keepalive.service -n 20
sudo systemctl start firetv-adb-keepalive.service   # force a reconnect
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| MCP returns `Entity not found` (HTTP 404) | AndroidTV config entry removed; orphaned entities in `core.entity_registry` | Re-add the integration (see [HA Integration](#ha-integration)) |
| `adb: device ... not found` | ADB connection dropped | `sudo systemctl start firetv-adb-keepalive.service` |
| `ServiceNotSupported: ... does not support action media_player.play_media` | Integration loaded but ADB never authenticated | Run `adb connect` against the device and accept the prompt on the TV |
| `media_player.turn_on` times out but state flips to `off` | TV woke from deep standby; HA call exceeded its window | Retry the action; `play_media` will also wake the device |

Logs to check:

- HA: the deployment's `home-assistant.log` (filter for `androidtv` / `adb`)
- Keepalive: `journalctl -u firetv-adb-keepalive.service`

---

*Last updated: v0.1.0*
