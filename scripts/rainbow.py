#!/usr/bin/env python3
import signal
import sys
import time
from types import FrameType

from home_assistant_lib import Light, LightOffPayload, LightOnPayload, hue_to_rgb

LIGHT = Light(entity_id="light.desk_lamp")
STEPS = 24
INTERVAL_S = 0.2
BRIGHTNESS = 255
SHUTDOWN_FADE_S = 1.0


def build_shutdown_handler(light: Light) -> "signal._HANDLER":
    def handler(_signum: int, _frame: FrameType | None) -> None:
        light.off(LightOffPayload(transition=SHUTDOWN_FADE_S))
        sys.exit(0)

    return handler


def main() -> int:
    handler = build_shutdown_handler(LIGHT)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    print(f"rainbow on {LIGHT.entity_id} — Ctrl-C to stop")

    i = 0
    while True:
        payload = LightOnPayload(rgb_color=hue_to_rgb((i % STEPS) / STEPS), brightness=BRIGHTNESS, transition=INTERVAL_S)
        _, error = LIGHT.on(payload)
        if error:
            print(error, file=sys.stderr)
            return 2

        i += 1
        time.sleep(INTERVAL_S)


if __name__ == "__main__":
    sys.exit(main())
