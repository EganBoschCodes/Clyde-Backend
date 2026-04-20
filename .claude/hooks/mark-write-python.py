#!/usr/bin/env python3
"""PostToolUse hook: drop a session marker when the write-python skill runs.

The companion PreToolUse hook (gate-py-edits.py) refuses to edit .py files
until this marker exists for the current session.
"""

import json
import re
import sys
from pathlib import Path


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0

    if data.get("tool_name") != "Skill":
        return 0

    skill = (data.get("tool_input") or {}).get("skill") or ""
    if not re.search(r"write-python$", skill):
        return 0

    session_id = data.get("session_id") or ""
    if not session_id:
        return 0

    Path(f"/tmp/claude-write-python-{session_id}").touch()
    return 0


if __name__ == "__main__":
    sys.exit(main())
