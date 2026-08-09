from __future__ import annotations

import json
import re
from typing import Any

WRITE_CMDS = ("create", "confirm", "research", "plan", "check", "finishing", "finish", "archive", "subtask",
              "sediment", "reindex", "init", "contract",
              # 子命令组下的写动作 (`prd write` / `task rename` / `claim` ...): 与上面同样改 .skein 状态,
              # 漏登记等于守门对它们放行
              "write", "add", "uncheck", "claim", "del", "fmt", "rename", "seam",
              "estimate", "priority", "deps", "parent", "repos", "start", "done", "fail")
# 取引擎名后**两**个词: `skein create` 与 `skein task create` 都要认。只取第一个词时
# `skein task create` 的 group(1) 是 "task", 不在 WRITE_CMDS 里 → 整条守门对 task 子命令组失明。
ENGINE_RE = re.compile(r"(?:skein\.py|spec\.py|\bskein\b|\bskein-spec\b)\s+([a-z-]+)(?:\s+([a-z-]+))?")
_GROUPS = {"task", "prd", "design", "config", "subtask", "spec"}


def is_write_command(command: str) -> bool:
    match = ENGINE_RE.search(command)
    if not match:
        return False
    first, second = match.group(1), match.group(2)
    if first in _GROUPS and second:
        return second in WRITE_CMDS or first in WRITE_CMDS
    return first in WRITE_CMDS


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
