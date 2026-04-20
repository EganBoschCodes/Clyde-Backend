#!/usr/bin/env python3
"""PreToolUse hook: block Edit/Write/MultiEdit on .py files until the
write-python skill has been invoked in this session.

Pairs with mark-write-python.py, which creates the marker file.
"""

import json
import sys
from pathlib import Path


REASON = (
    "Run the /write-python skill before editing .py files in this repo — "
    "it loads the Python patterns (Result type, Pydantic, file structure) "
    "we follow here."
)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0

    path = (data.get("tool_input") or {}).get("file_path") or ""
    if not path.endswith(".py"):
        return 0

    session_id = data.get("session_id") or ""
    marker = Path(f"/tmp/claude-write-python-{session_id}")
    if marker.exists():
        return 0

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": REASON,
            }
        },
        sys.stdout,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
