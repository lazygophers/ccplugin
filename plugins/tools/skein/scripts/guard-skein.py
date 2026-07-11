#!/usr/bin/env python3
"""SKEIN PreToolUse guard: 硬阻 AI 直接读写 .skein/ 的脚本管理文件。

四个文件全归 skein.py 维护, AI 读写全挡 (读态经命令 stdout, 非读文件):
  .skein/task.json            顶层状态 (focus)
  .skein/task.md              顶层看板
  .skein/task/<id>/task.json  单 task 记录 + subtask DAG
  .skein/task/<id>/task.md    单 task 子任务看板
判定: 路径落在 .skein/ 下且 basename ∈ {task.json, task.md} → 挡 (含归档路径)。
planning 工件 (prd/design/implement/journal .md) 不在此列, 放行。

命中则 exit 2 (block) 并把替代方式写 stderr。
"""
import json
import os
import sys

BLOCKED = {"task.json", "task.md"}


def main() -> int:
    try:
        d = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    fp = d.get("tool_input", {}).get("file_path", "")
    if not fp:
        return 0
    parts = fp.replace("\\", "/").split("/")
    if ".skein" in parts and os.path.basename(fp) in BLOCKED:
        print(
            "禁直接读写 .skein/ 的 task.json / task.md — 均由 skein.py 维护。"
            "取态: `skein.py current` / `list` / `subtask list <id>` / `subtask ready <id>`; "
            "改态: create/start/finish/archive/subtask。",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
