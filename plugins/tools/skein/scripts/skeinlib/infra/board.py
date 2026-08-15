"""markdown 看板渲染 — **纯函数: 吃数据, 返字符串, 不碰文件**。

写盘归 `store.TaskStore` (它是 task.json 的唯一写入口, 顺手刷对应的 .md)。这层不反向调 store,
所以依赖是单向的 —— 从前 `_board()` 自己调 `_render_tasks()` 又被 `_sync()` 调, 拆包时就是个环。

渲染出的三份 .md 全部 git 忽略, 由脚本维护, AI 禁直接读写 (取态走 CLI stdout)。
"""
from __future__ import annotations

from typing import Any

from skeinlib.task.dag import _sub_pct

# 状态直接落英文 enum 值 (中文展示归前端 assets/nextjs/src/components/status.tsx)


def render_board(tasks: list[dict[str, Any]], wt_shown: bool) -> str:
    """顶层看板 `.skein/task.md`。"""
    empty = "| - | - | - | - | - |" if wt_shown else "| - | - | - | - |"

    def row(t: dict[str, Any]) -> str:
        deps = ",".join(t.get("deps", [])) or "-"
        base = f"| {t['id']} | {t['name']} | {t['status']} | {deps} |"
        return f"{base} {t.get('worktree') or '-'} |" if wt_shown else base

    body = "\n".join(row(t) for t in tasks) if tasks else empty
    head = ("| id | 名称 | 状态 | 前置 | worktree |\n|---|---|---|---|---|"
            if wt_shown else "| id | 名称 | 状态 | 前置 |\n|---|---|---|---|")
    return (
        "# SKEIN 看板\n\n"
        "> task.json 变更即自动渲染, 禁直接编辑。无 task 级 focus — 进行中 task 皆可并行。\n\n"
        f"{head}\n"
        f"{body}\n"
    )


def render_task_board(t: dict[str, Any], work_active: int, gate_active: int) -> str:
    """单 task 的子任务看板 `.skein/task/<id>/task.md`。

    两池上限分两行展示 (design.md §3): work = exec+research subtask 并发, gate = check+finishing
    task 并发。此文件只列 subtask (work 池对象), gate 池是 task 级概念, 这里仅同时报上限供对照。
    """
    rows: list[str] = []
    for s in t.get("subtasks", []):
        deps = ",".join(s.get("depends_on", [])) or "-"
        chk = "; ".join(s.get("acceptance", [])) or "-"
        sk = ",".join(s.get("skills", [])) or "-"
        rows.append(f"| {s['sid']} | {s['name']} | {s['status']} | {_sub_pct(s)}% | {sk} | {deps} | {chk} |")
    body = "\n".join(rows) if rows else "| - | - | - | - | - | - | - |"
    deps = ",".join(t.get("deps", [])) or "-"
    return (
        f"# SKEIN 子任务看板 — {t['id']} {t['name']}\n\n"
        "> 经 `skein subtask` 渲染, 禁直接读写; 取态用 `skein subtask list <id>`。\n\n"
        f"前置 task: {deps}\n\n"
        "| sid | 名称 | 状态 | 进度 | skills | 依赖 | 验收标准 |\n"
        "|---|---|---|---|---|---|---|\n"
        f"{body}\n\n"
        f"work 池上限: {work_active}\n"
        f"gate 池上限: {gate_active}\n"
    )
