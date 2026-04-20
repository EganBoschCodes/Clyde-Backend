#!/usr/bin/env python3
"""PostToolUse hook: run pyright after a .py edit and feed any errors back.

Runs pyright on the whole project (cheap — the project is small) and
injects a summary of any errors into the model context via
`hookSpecificOutput.additionalContext`.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


MAX_ERRORS_REPORTED = 20


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0

    tool_input = data.get("tool_input") or {}
    path = tool_input.get("file_path") or ""
    if not path.endswith(".py"):
        return 0

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    env = os.environ.copy()
    local_bin = str(Path.home() / ".local" / "bin")
    env["PATH"] = f"{local_bin}:{env.get('PATH', '')}"

    try:
        result = subprocess.run(
            ["pyright", "--outputjson"],
            cwd=project_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 0

    try:
        report = json.loads(result.stdout)
    except ValueError:
        return 0

    errors = [
        d for d in report.get("generalDiagnostics", [])
        if d.get("severity") == "error"
    ]
    if not errors:
        return 0

    lines: list[str] = []
    for d in errors[:MAX_ERRORS_REPORTED]:
        file_path = d.get("file", "")
        start = (d.get("range") or {}).get("start") or {}
        line = int(start.get("line", 0)) + 1
        col = int(start.get("character", 0)) + 1
        raw_msg = d.get("message") or ""
        msg = raw_msg.splitlines()[0] if raw_msg else ""
        rule = d.get("rule", "")
        rel = os.path.relpath(file_path, project_dir) if file_path else "?"
        suffix = f" ({rule})" if rule else ""
        lines.append(f"{rel}:{line}:{col} {msg}{suffix}")

    extra = ""
    if len(errors) > MAX_ERRORS_REPORTED:
        extra = f"\n...and {len(errors) - MAX_ERRORS_REPORTED} more"

    context = (
        f"pyright found {len(errors)} type error(s) after your edit:\n"
        + "\n".join(lines)
        + extra
    )

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": context,
            }
        },
        sys.stdout,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
