#!/usr/bin/env python3
"""SKEIN PreToolUse guard: 硬阻直接访问 .skein/ 的脚本管理文件。

  task.md    看板 — 仅挡写 (Edit/Write/MultiEdit); 读放行 (AI 看板本就要读)。
  state.json 状态 — 读写全挡; 状态只经 skein.py (current 取 / create/start/finish 改)。

读 stdin hook payload, 命中则 exit 2 (block) 并把提示写 stderr。
"""
import json
import sys


def main() -> int:
    try:
        d = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    tool = d.get("tool_name", "")
    fp = d.get("tool_input", {}).get("file_path", "")

    if fp.endswith("/.skein/state.json"):
        print(
            "禁直接读写 .skein/state.json — 状态经 skein.py 管理。"
            "取 focus 用 `skein.py current`, 改用 create/start/finish。",
            file=sys.stderr,
        )
        return 2
    if fp.endswith("/.skein/task.md") and tool in ("Edit", "Write", "MultiEdit"):
        print(
            "禁直接编辑 .skein/task.md — 看板经 `skein.py board` 渲染。"
            "改 task 状态用 skein.py create/start/finish。",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
