#!/usr/bin/env python3
import signal
import sys
import time
from types import FrameType

from home_assistant_lib import RGB, Light, LightOnPayload

LIGHT = Light(entity_id="light.desk_lamp")
COLORS: list[RGB] = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (255, 0, 255),
    (0, 255, 255),
]
INTERVAL_S = 0.25
BRIGHTNESS = 255
TRANSITION_S = 0.0


def build_shutdown_handler(light: Light) -> "signal._HANDLER":
    def handler(_signum: int, _frame: FrameType | None) -> None:
        light.off()
        sys.exit(0)

    return handler


def main() -> int:
    handler = build_shutdown_handler(LIGHT)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    print(f"strobing {LIGHT.entity_id} — Ctrl-C to stop")

    i = 0
    while True:
        payload = LightOnPayload(rgb_color=COLORS[i % len(COLORS)], brightness=BRIGHTNESS, transition=TRANSITION_S)
        _, error = LIGHT.on(payload)
        if error:
            print(error, file=sys.stderr)
            return 2

        i += 1
        time.sleep(INTERVAL_S)


if __name__ == "__main__":
    sys.exit(main())
