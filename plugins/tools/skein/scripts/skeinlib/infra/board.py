"""markdown 看板渲染 — **纯函数: 吃数据, 返字符串, 不碰文件**。

写盘归 `store.TaskStore` (它是 task.json 的唯一写入口, 顺手刷对应的 .md)。这层不反向调 store,
所以依赖是单向的 —— 从前 `_board()` 自己调 `_render_tasks()` 又被 `_sync()` 调, 拆包时就是个环。

渲染出的三份 .md 全部 git 忽略, 由脚本维护, AI 禁直接读写 (取态走 CLI stdout)。
"""
from __future__ import annotations

from typing import Any

from skeinlib.task.dag import _sub_pct, _task_pct
from skeinlib.task.model import SUBTASK_STATUS_DISPLAY, TASK_STATUS_DISPLAY, SubtaskStatus, TaskStatus


def _task_status_label(value: Any) -> str:
    try:
        return TASK_STATUS_DISPLAY[TaskStatus(value)]
    except ValueError:
        return str(value)


def _subtask_status_label(value: Any) -> str:
    try:
        return SUBTASK_STATUS_DISPLAY[SubtaskStatus(value)]
    except ValueError:
        return str(value)


def render_board(tasks: list[dict[str, Any]], wt_shown: bool) -> str:
    """顶层看板 `.skein/task.md`。

    supertask 作分组头, 其 child 缩进列在下面; 其余 (独立 task / 孤儿 parent) 保持扁平行。
    无 supertask 时输出**逐字**等于旧扁平版 —— 零增量是关键回归点, 改这里先看 views_golden。
    """
    by_parent: dict[str, list[dict[str, Any]]] = {}
    for t in tasks:
        if t.get("parent"):
            by_parent.setdefault(t["parent"], []).append(t)
    supertasks = [t for t in tasks if t.get("kind") == "supertask"]
    empty = "| - | - | - | - | - |" if wt_shown else "| - | - | - | - |"

    def row(t: dict[str, Any]) -> str:
        deps = ",".join(t.get("deps", [])) or "-"
        base = f"| {t['id']} | {t['name']} | {_task_status_label(t['status'])} | {deps} |"
        return f"{base} {t.get('worktree') or '-'} |" if wt_shown else base

    if not supertasks:
        body = "\n".join(row(t) for t in tasks) if tasks else empty
    else:
        lines: list[str] = []
        seen: set[str] = set()
        for st in supertasks:
            lines.append(row(st))
            seen.add(st["id"])
            for c in by_parent.get(st["id"], []):
                crow = (f"| ↳ {c['id']} | {c['name']} | {_task_status_label(c['status'])} | "
                        f"{','.join(c.get('deps', [])) or '-'} |")
                if wt_shown:
                    crow += f" {c.get('worktree') or '-'} |"
                lines.append(crow)
                seen.add(c["id"])
        rest = [t for t in tasks if t["id"] not in seen]
        lines.extend(row(t) for t in rest)  # 独立/孤儿 task 原样平铺, 不强制分组
        body = "\n".join(lines) if lines else empty
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
        rows.append(f"| {s['sid']} | {s['name']} | {_subtask_status_label(s['status'])} | {_sub_pct(s)}% | {sk} | {deps} | {chk} |")
    body = "\n".join(rows) if rows else "| - | - | - | - | - | - | - |"
    deps = ",".join(t.get("deps", [])) or "-"
    parent = t.get("parent") or "-"
    return (
        f"# SKEIN 子任务看板 — {t['id']} {t['name']}\n\n"
        "> 经 `skein subtask` 渲染, 禁直接读写; 取态用 `skein subtask list <id>`。\n\n"
        f"前置 task: {deps}\n"
        f"父 task: {parent}\n\n"
        "| sid | 名称 | 状态 | 进度 | skills | 依赖 | 验收标准 |\n"
        "|---|---|---|---|---|---|---|\n"
        f"{body}\n\n"
        f"work 池上限: {work_active}\n"
        f"gate 池上限: {gate_active}\n"
    )


def render_vision(st: dict[str, Any], children: list[dict[str, Any]]) -> str:
    """supertask 聚合看板 `.skein/task/<id>/vision.md` — 汇总 child 状态与加权完成率。

    整体完成率 = child `_task_pct` 均值。归档时随目录一起移走 (文件在 task/<id>/ 下)。
    """
    rows = []
    for c in children:
        subs = c.get("subtasks", [])
        sdone = sum(1 for s in subs if s.get("status") == SubtaskStatus.DONE)
        sratio = f"{sdone}/{len(subs)}" if subs else "-"
        rows.append(f"| {c['id']} | {c['name']} | {_task_status_label(c['status'])} | {sratio} | {_task_pct(c)}% |")
    body = "\n".join(rows) if rows else "| - | - | - | - | - |"
    overall = (sum(_task_pct(c) for c in children) // len(children)) if children else 0
    done_n = sum(1 for c in children if c.get("status") == TaskStatus.DONE)
    return (
        f"# SKEIN supertask 聚合看板 — {st['id']} {st.get('name') or st['id']}\n\n"
        "> 脚本渲染, 禁直接编辑; child task 状态变更即自动刷。整体完成率 = child _task_pct 均值。\n\n"
        f"**整体进度**: {overall}% · **child**: {done_n}/{len(children)} 已完成\n\n"
        "| child | 名称 | 状态 | subtask 完成 | 进度 |\n"
        "|---|---|---|---|---|\n"
        f"{body}\n"
    )
