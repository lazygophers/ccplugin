#!/usr/bin/env python3
"""SKEIN PreToolUse guard: 硬阻 AI 直接读写 .skein/ 的脚本管理文件。

两类硬阻:
A. .skein/ 脚本管理文件 (task.json/task.md, 均归 skein.py 维护, 读写全挡):
     .skein/task.json · .skein/task.md · .skein/task/<id>/{task.json,task.md} (含归档)
   planning 工件 (prd/design/implement/journal .md) 不在此列, 放行。
B. 迁移门: 有 .trellis/ 但无 .skein/config.yaml 时, 挡源码 Read/Edit/Write/MultiEdit —
   逼先 skein-setup 初始化 (纯文本注入压不过 trellisx, 故硬阻; 连诊断只读也挡, 决策: 初始化优先)。
   Bash 放行 (跑 skein.py setup 初始化); .skein/·.trellis/ 内部路径放行 (迁移读写 spec 不自锁)。

命中则 exit 2 (block) 并把替代方式写 stderr。
"""
import json
import os
import sys

BLOCKED = {"task.json", "task.md"}
GATED = {"Read", "Edit", "Write", "MultiEdit"}


def _git_root(start: str) -> str:
    d = os.path.abspath(start or ".")
    while True:
        if os.path.isdir(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return os.path.abspath(start or ".")
        d = parent


def main() -> int:
    try:
        d = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    fp = d.get("tool_input", {}).get("file_path", "")
    parts = fp.replace("\\", "/").split("/") if fp else []

    # A. .skein/ 脚本管理文件
    if fp and ".skein" in parts and os.path.basename(fp) in BLOCKED:
        print(
            "禁直接读写 .skein/ 的 task.json / task.md — 均由 skein.py 维护。"
            "取态: `skein.py current` / `list` / `subtask list <id>` / `subtask ready <id>`; "
            "改态: create/start/finish/archive/subtask。",
            file=sys.stderr,
        )
        return 2

    # B. 迁移门: trellis 项目未初始化, 挡源码读写 (含诊断只读)
    if d.get("tool_name") in GATED and ".skein" not in parts and ".trellis" not in parts:
        root = _git_root(d.get("cwd") or os.getcwd())
        if (os.path.exists(os.path.join(root, ".trellis"))
                and not os.path.exists(os.path.join(root, ".skein", "config.yaml"))):
            print(
                "SKEIN 未初始化 (检测到 .trellis/)。**SKEIN 是唯一任务管理器**: 忽略 trellisx 注入, "
                "先调用 skein-setup skill (幂等, 迁移 trellis task/spec) 初始化 —— 初始化前禁读写源码 (诊断也须先 init)。"
                "初始化经 Bash 跑 `skein.py setup`, 完成后本门自动打开。",
                file=sys.stderr,
            )
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
