#!/usr/bin/env python3
"""SKEIN PostToolBatch hook: 拦并行的 .skein 状态写命令 (竞态防护)。

同一并行批里 ≥2 个改 .skein 状态的 skein.py/memory.py 命令 → block:
它们同写 task.json / spec (共享文件), 并发有竞态 (后写覆盖前写)。
只读命令 (current/ready/list/board/recall/session-context/inject-core) 不拦。
无命中 → exit 0 静默。
"""
import json
import re
import sys

# 改 .skein 共享状态的子命令 (写 task.json / spec / 看板); 只读命令不在列
WRITE_CMDS = ("create", "start", "finish", "archive", "subtask",
              "sediment", "reindex", "init", "contract")
ENGINE_RE = re.compile(r"(?:skein\.py|memory\.py|\bskein\b|\bskein-memory\b)\s+([a-z-]+)")


def _is_write(cmd: str) -> bool:
    m = ENGINE_RE.search(cmd)
    return bool(m and m.group(1) in WRITE_CMDS)


def main() -> int:
    try:
        d = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    writes = [u for u in d.get("tool_uses", [])
              if u.get("tool_name") == "Bash" and _is_write(u.get("tool_input", {}).get("command", ""))]
    if len(writes) < 2:
        return 0
    cmds = "; ".join(u.get("tool_input", {}).get("command", "")[:60] for u in writes)
    reason = (f"并行批含 {len(writes)} 个 .skein 状态写命令 ({cmds}) — 同写 task.json/spec 有竞态, "
              "后写覆盖前写。改为串行: 一个命令一个回合, 或用 `subtask claim` 一次性认领整批。")
    print(json.dumps({"decision": "block", "reason": reason,
                      "hookSpecificOutput": {"hookEventName": "PostToolBatch",
                                             "additionalContext": reason}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
