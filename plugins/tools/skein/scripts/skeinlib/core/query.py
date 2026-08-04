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
from skeinlib.task.model import (PRIORITY_DEFAULT, SubtaskStatus, TaskStatus, _STATUS_ALIAS)

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
        if st:
            if st in ("open", "unfinished", "未完成"):
                tasks = [t for t in tasks if t["status"] != TaskStatus.DONE]
            else:
                wanted = {_STATUS_ALIAS.get(x.strip(), x.strip()) for x in st.split(",")}
                bad = wanted - {TaskStatus.PENDING, TaskStatus.RESEARCH, TaskStatus.ACTIVE, TaskStatus.CHECK, TaskStatus.FINISHING, TaskStatus.DONE}
                if bad:
                    raise SkeinError(
                        f"未知 status: {', '.join(sorted(bad))} — 可选 "
                        f"待处理/调研中/进行中/检查中/收尾中/已完成 "
                        f"(或 pending/research/active/check/finishing/done), open=全部未完成")
                tasks = [t for t in tasks if t["status"] in wanted]
        return {"tasks": [self._brief(t) for t in tasks]}
