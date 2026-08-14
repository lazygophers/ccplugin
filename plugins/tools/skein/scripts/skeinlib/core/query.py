"""`Query` — 只读投影: ready / status / list。

全部**不写盘**, 所以 `cli.main` 不给这几条命令加工作区写锁 (见 cli.py 的 `MUTATING`)。
新增命令若会写盘, 别放这个类 —— 放进来就绕过锁了。
"""
from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from skeinlib.core.workspace import Workspace

from skeinlib.task.dag import _sub_pct, _task_pct
from skeinlib.utils.errors import SkeinError
from skeinlib.task.model import (PRIORITY_DEFAULT, STATUS_ACTIVE, SubtaskPhase, SubtaskStatus,
                                 TaskStatus, _STATUS_ALIAS, now)

from skeinlib.infra.worktree import worktrees_of


class Query:
    """只读查询与投影。"""

    def __init__(self, ws: "Workspace") -> None:
        self.ws = ws

    def current(self, a: argparse.Namespace) -> dict[str, Any]:
        active = self.ws.store.active()
        wt_col = self.ws._wt_shown()
        return {
            "tasks": [{
                "id": t["id"],
                "status": t["status"],
                "name": t["name"],
                **({"worktree": t.get("worktree") or None} if wt_col else {}),
            } for t in active],
        }

    def status_overview(self, a: argparse.Namespace) -> dict[str, Any] | None:
        """全局运行态概览: 两池占用 + 执行中 subtask + 各状态 task 统计。

        默认返回结构化 dict (走 cli 统一 JSON 输出); `--pretty` rich 渲染自打印, 返回 None。
        """
        tasks = self.ws.store.all_tasks()
        cfg = self.ws.config()
        work_cap = cfg["pools"]["work"]
        gate_cap = cfg["pools"]["gate"]
        tnow = now()

        # 执行中 subtask: 全部 active task (进行中/调研中/收尾中) 内 status=running
        running_subs: list[dict[str, Any]] = []
        ready_cnt = 0
        for t in tasks:
            if t["status"] not in STATUS_ACTIVE:
                continue
            subs = t.get("subtasks", [])
            done = {s["sid"] for s in subs if s["status"] == SubtaskStatus.DONE}
            for s in subs:
                if s["status"] == SubtaskStatus.RUNNING:
                    started = s.get("started")
                    running_subs.append({
                        "tid": t["id"], "sid": s["sid"], "name": s.get("name", s["sid"]),
                        "phase": s.get("phase", SubtaskPhase.EXEC),
                        "started": started,
                        "elapsed_min": round((tnow - started) / 60, 1) if started else None,
                        "pct": _sub_pct(s),
                    })
                elif (s["status"] == SubtaskStatus.PENDING
                      and all(d in done for d in s.get("depends_on", []))):
                    ready_cnt += 1  # 就绪待派 (依赖全 done, 不受槽限的展示口径)

        by_status: dict[str, int] = {}
        for t in tasks:
            by_status[t["status"]] = by_status.get(t["status"], 0) + 1
        gate_tasks = [{"id": t["id"], "name": t.get("name", t["id"]), "status": t["status"]}
                      for t in tasks if t["status"] in (TaskStatus.CHECK, TaskStatus.FINISHING)]
        active_tasks = [{"id": t["id"], "name": t.get("name", t["id"]), "status": t["status"],
                         "pct": _task_pct(t),
                         "sdone": sum(1 for s in t.get("subtasks", []) if s["status"] == SubtaskStatus.DONE),
                         "stotal": len(t.get("subtasks", []))}
                        for t in tasks if t["status"] in STATUS_ACTIVE]

        data = {
            "pool": {"work": {"running": len(running_subs), "capacity": work_cap},
                     "gate": {"running": len(gate_tasks), "capacity": gate_cap}},
            "tasks": {"total": len(tasks), "by_status": by_status},
            "running_subtasks": running_subs,
            "ready_pending": ready_cnt,
            "gate_tasks": gate_tasks,
            "active_tasks": active_tasks,
            "next": ("skein flow run" if ready_cnt and len(running_subs) < work_cap
                     else "等 subtask done 释放槽" if len(running_subs) >= work_cap
                     else "skein list --status plan"),
        }

        if not getattr(a, "pretty", False):
            return data
        self._render_status(data)
        return None

    def _render_status(self, d: dict[str, Any]) -> None:
        # rich 人读渲染 (doctor/board 同款自打印模式)。cli 返回 None → 不再打 JSON。
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        console = Console()
        p = d["pool"]
        console.print(Panel.fit(
            f"work 池 [cyan]{p['work']['running']}/{p['work']['capacity']}[/cyan] · "
            f"gate 池 [cyan]{p['gate']['running']}/{p['gate']['capacity']}[/cyan]",
            title="SKEIN 运行态", border_style="blue"))
        st = d["tasks"]["by_status"]
        order = [TaskStatus.ACTIVE, TaskStatus.RESEARCH, TaskStatus.CHECK,
                 TaskStatus.FINISHING, TaskStatus.PENDING, TaskStatus.DONE]
        disp = {"active": "进行中", "research": "调研中", "check": "检查中",
                "finishing": "收尾中", "pending": "待处理", "done": "已完成"}
        parts = [f"{disp.get(k, k)} {v}" for k in order if (v := st.get(k))]
        console.print("  " + " · ".join(parts) if parts else "  无 task")

        if d["running_subtasks"]:
            console.print("\n[bold]执行中 subtask:[/bold]")
            table = Table(show_header=True, box=None, padding=(0, 2))
            for col, style in (("tid", "cyan"), ("sid", "cyan"), ("名称", None),
                               ("阶段", "yellow"), ("进度", "green"), ("已跑", "dim")):
                table.add_column(col, style=style)
            for s in d["running_subtasks"]:
                elapsed = f"{s['elapsed_min']}m" if s["elapsed_min"] is not None else "-"
                table.add_row(s["tid"], s["sid"], s["name"], s["phase"],
                              f"{s['pct']}%", elapsed)
            console.print(table)
        else:
            console.print("\n[dim]无执行中 subtask[/dim]")

        if d["gate_tasks"]:
            gt = " · ".join(f"{t['id']}({t['status']})" for t in d["gate_tasks"])
            console.print(f"\n[bold]检查/收尾中:[/bold] {gt}")
        console.print(f"\n[dim]就绪待派: {d['ready_pending']} → {d['next']}[/dim]")


    def ready(self, a: argparse.Namespace) -> dict[str, Any]:
        picked = [t for t in self.ws.store.all_tasks()
                 if t["status"] == TaskStatus.PENDING
                 and not any(self.ws._dep_unfinished(d) for d in t["deps"])]
        return {
            "tasks": [{"id": t["id"], "name": t["name"], "deps": t["deps"]} for t in picked],
        }

    def status(self, a: argparse.Namespace) -> dict[str, Any]:
        t = self.ws.store.load(a.tid)
        subs = t.get("subtasks", [])
        if getattr(a, "sid", None):
            s = next((x for x in subs if x["sid"] == a.sid), None)
            if not s:
                raise SkeinError(f"subtask 不存在: {a.tid}/{a.sid} "
                                 f"(现有: {', '.join(x['sid'] for x in subs) or '无'})")
            return {"task": t["id"], "subtask": s}
        return {"task": self._brief(t)}

    def _brief(self, t: dict[str, Any]) -> dict[str, Any]:
        subs = t.get("subtasks", [])
        cnt = [0, 0, 0, 0]
        idx: dict[str, int] = {SubtaskStatus.DONE: 0, SubtaskStatus.RUNNING: 1, SubtaskStatus.PENDING: 2, SubtaskStatus.FAILED: 3}
        for s in subs:
            i = idx.get(s["status"])
            if i is not None:
                cnt[i] += 1
        pct = _task_pct(t)
        ready = t["status"] == TaskStatus.PENDING and not any(
            self.ws._dep_unfinished(d) for d in t.get("deps", []))
        wt_shown = self.ws._wt_shown()
        return {"id": t["id"], "status": t["status"], "name": t.get("name", ""),
                "desc": t.get("desc", ""), "deps": t.get("deps", []),
                "repos": t.get("repos", []),
                "worktree": (t.get("worktree") or None) if wt_shown else None,
                "worktrees": [{"repo": w["repo"], "wt": w["wt"]} for w in worktrees_of(t)] if wt_shown else [],
                "priority": t.get("priority") or PRIORITY_DEFAULT,
                "pct": pct, "subs": cnt, "ready": ready}

    def list_(self, a: argparse.Namespace) -> dict[str, Any]:
        tasks = self.ws.store.all_tasks()
        st = (getattr(a, "status", None) or "").strip()
        # --status 的阶段名别名 (与回复前缀 PHASE_OF 同一套语义): plan→待处理, exec→进行中, finish→收尾中
        phase_alias = {"plan": TaskStatus.PENDING, "exec": TaskStatus.ACTIVE,
                       "finish": TaskStatus.FINISHING}
        if st:
            if st in ("all", "全部", "*"):
                pass  # 不筛; `all` 是自然猜测, 不收就只会换来一次重试
            elif st in ("open", "plan", "待处理"):
                # open = plan 阶段 (还没开工的 task); 「全部未完成」走 unfinished
                tasks = [t for t in tasks if t["status"] == TaskStatus.PENDING]
            elif st in ("unfinished", "未完成"):
                tasks = [t for t in tasks if t["status"] != TaskStatus.DONE]
            else:
                wanted = {phase_alias.get(x.strip(), None) or _STATUS_ALIAS.get(x.strip(), x.strip())
                          for x in st.split(",")}
                bad = wanted - {TaskStatus.PENDING, TaskStatus.RESEARCH, TaskStatus.ACTIVE, TaskStatus.CHECK, TaskStatus.FINISHING, TaskStatus.DONE}
                if bad:
                    raise SkeinError(
                        f"未知 status: {', '.join(sorted(bad))} — 可选 "
                        f"待处理/调研中/进行中/检查中/收尾中/已完成 "
                        f"(或 plan/research/exec/check/finishing/finish/done), "
                        f"open=plan 阶段, unfinished=全部未完成, all=不筛")
                tasks = [t for t in tasks if t["status"] in wanted]
        return {"tasks": [self._brief(t) for t in tasks]}
