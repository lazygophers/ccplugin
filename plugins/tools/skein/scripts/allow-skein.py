#!/usr/bin/env python3
"""SKEIN PermissionRequest hook: 对 .skein/ 自有内容操作默认同意, 免逐次授权打断。

放行 (behavior=allow):
  - Bash 调本插件引擎: 命令含 skein.py / memory.py / 短命令 `skein `/`skein-memory `
  - Edit/Write/Read: 落 .skein/ 且非脚本管理文件 (task.json/task.md 归 guard 硬阻, 不放行)
其余 → 静默 (不输出 decision, 交默认授权流程)。
allow 不覆盖 deny 规则, 也不覆盖 guard-skein 的 PreToolUse 阻断 (安全内核不放宽)。
"""
import json
import os
import sys

BLOCKED = {"task.json", "task.md"}  # 脚本管理文件, 归 guard, 不由本 hook 放行
ENGINE = ("skein.py", "memory.py", "skein ", "skein-memory ")


def _allow():
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {"behavior": "allow"}}}))


def main() -> int:
    try:
        d = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    tool = d.get("tool_name", "")
    ti = d.get("tool_input", {})
    if tool == "Bash":
        if any(k in ti.get("command", "") for k in ENGINE):
            _allow()
        return 0
    if tool in ("Edit", "Write", "Read"):
        fp = ti.get("file_path", "")
        parts = fp.replace("\\", "/").split("/")
        if ".skein" in parts and os.path.basename(fp) not in BLOCKED:
            _allow()
    return 0


if __name__ == "__main__":
    sys.exit(main())
