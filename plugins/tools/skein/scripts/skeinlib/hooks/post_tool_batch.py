from __future__ import annotations

import json
import re
from typing import Any

WRITE_CMDS = ("create", "confirm", "research", "plan", "check", "finishing", "finish", "archive", "subtask",
              "sediment", "reindex", "init", "contract")
ENGINE_RE = re.compile(r"(?:skein\.py|spec\.py|\bskein\b|\bskein-spec\b)\s+([a-z-]+)")


def is_write_command(command: str) -> bool:
    match = ENGINE_RE.search(command)
    return bool(match and match.group(1) in WRITE_CMDS)


def cmd_batch(payload: dict[str, Any]) -> int:
    writes = [tool_use for tool_use in payload.get("tool_uses", [])
              if tool_use.get("tool_name") == "Bash"
              and is_write_command(tool_use.get("tool_input", {}).get("command", ""))]
    if len(writes) < 2:
        return 0
    commands = "; ".join(tool_use.get("tool_input", {}).get("command", "")[:60] for tool_use in writes)
    reason = (f"并行批含 {len(writes)} 个 .skein 状态写命令 ({commands}) — 同写 task.json/spec 有竞态, "
              "后写覆盖前写。改为串行: 一个命令一个回合, 或用 `subtask claim` 一次性认领整批。")
    print(json.dumps({"decision": "block", "reason": reason,
                      "hookSpecificOutput": {"hookEventName": "PostToolBatch",
                                             "additionalContext": reason}}))
    return 0


_is_write = is_write_command

__all__ = ["WRITE_CMDS", "ENGINE_RE", "cmd_batch", "is_write_command", "_is_write"]
