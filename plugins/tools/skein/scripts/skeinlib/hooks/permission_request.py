from __future__ import annotations

import json
import os
from typing import Any


def allow_permission() -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {"behavior": "allow"}}}))


def cmd_permission(payload: dict[str, Any]) -> int:
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    if tool_name == "Bash":
        if any(engine in tool_input.get("command", "") for engine in ("skein.py", "spec.py", "skein ", "skein-spec ")):
            allow_permission()
        return 0
    if tool_name in ("Edit", "Write", "Read"):
        file_path = tool_input.get("file_path", "")
        if ".skein" in file_path.replace("\\", "/").split("/") and os.path.basename(file_path) not in {"task.json", "task.md", "prd.md"}:
            allow_permission()
    return 0


__all__ = ["allow_permission", "cmd_permission"]
