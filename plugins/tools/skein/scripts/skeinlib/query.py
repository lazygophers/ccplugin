"""`Query` — 只读投影: current / ready / status / list。

全部**不写盘**, 所以 `cli.main` 不给这几条命令加工作区写锁 (见 cli.py 的 `MUTATING`)。
新增命令若会写盘, 别放这个类 —— 放进来就绕过锁了。
"""
from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from skeinlib.workspace import Workspace

from skeinlib.dag import _sub_pct, _task_pct
from skeinlib.errors import SkeinError
from skeinlib.model import (SS_DONE, SS_FAILED, SS_PENDING, SS_RUNNING, S_ACTIVE, S_CHECK,
                            S_DONE, S_PENDING, S_READY, _STATUS_ALIAS)
from skeinlib.views import _fmt_ts
from skeinlib.worktree import worktrees_of

import json


class Query:
    """只读查询与投影。"""

    def __init__(self, ws: "Workspace") -> None:
        self.ws = ws

    def current(self, a: argparse.Namespace) -> None:
        active = self.ws.store.active()
        if not active:
            print("无 active task")
            return
        wt_col = self.ws._wt_shown()
        for t in active:
            if wt_col:
                print(f"{t['id']}\t{t['status']}\t{t['name']}\t{t.get('worktree') or '-'}")
            else:
                print(f"{t['id']}\t{t['status']}\t{t['name']}")

    def ready(self, a: argparse.Namespace) -> None:
        # task 级可启动批 (脚本算, 非 AI 判): 就绪态 (已过 confirm 门) + 前置全 done + 有空闲 active 槽位。
        # 与 subtask ready 同构, 但只读预览 (start 才占槽); task 无写集字段, 故不算写集冲突。
        slots = self.ws.config()["max_active"] - len(self.ws.store.active())
        if slots <= 0:
            print(f"无空闲 active 槽 (上限 {self.ws.config()['max_active']} 已满) — 先 finish 一个再 start")
            return
        picked: list[dict[str, Any]] = []
        for t in self.ws.store.all_tasks():
            if t["status"] != S_READY:
                continue
            undone = [d for d in t["deps"] if self.ws._dep_unfinished(d)]
            if undone:
                continue
            picked.append(t)
            if len(picked) >= slots:
                break
        if not picked:
            print("无可启动 task (就绪态均有未完成前置, 或无就绪态 — 待处理须先 skein confirm)")
            return
        print("可启动 task (只读预览, 激活用 `skein.py start <id>`):")
        for t in picked:
            deps = ",".join(t["deps"]) or "-"
            print(f"{t['id']}\t{t['name']}\t前置: {deps}")

    def status(self, a: argparse.Namespace) -> None:
        # 只读查态: `status <tid>` 出 task 态 + subtask 汇总; `status <tid> <sid>` 出单个 subtask 明细。
        t = self.ws.store.load(a.tid)
        subs = t.get("subtasks", [])
        if getattr(a, "sid", None):
            s = next((x for x in subs if x["sid"] == a.sid), None)
            if not s:
                raise SkeinError(f"subtask 不存在: {a.tid}/{a.sid} "
                                 f"(现有: {', '.join(x['sid'] for x in subs) or '无'})")
            if getattr(a, "json", False):
                print(json.dumps(s, ensure_ascii=False, separators=(",", ":")))
                return
            deps = ",".join(s.get("depends_on", [])) or "-"
            chk = "; ".join(s.get("验收", [])) or "-"
            sk = ",".join(s.get("skills", [])) or "-"
            print(f"task\t{t['id']}\t{t['status']}\t{t['name']}")
            print(f"subtask\t{s['sid']}\t{s['status']}\t{_sub_pct(s)}%\t{s['name']}")
            print(f"desc\t{s.get('desc') or '-'}")
            print(f"依赖\t{deps}\tskills:{sk}")
            print(f"验收\t{chk}")
            print(f"时间\tcreated:{_fmt_ts(s.get('created'))}\t"
                  f"started:{_fmt_ts(s.get('started'))}\tfinished:{_fmt_ts(s.get('finished'))}")
            return
        if getattr(a, "json", False):
            print(json.dumps(self._brief(t), ensure_ascii=False, separators=(",", ":")))
            return
        pct = _task_pct(t)
        deps = ",".join(t.get("deps", [])) or "-"
        print(f"task\t{t['id']}\t{t['status']}\t{pct}%\t{t['name']}")
        if self.ws._wt_shown():
            print(f"worktree\t{t.get('worktree') or '-'}\t前置:{deps}")
        else:
            print(f"前置:{deps}")
        if not subs:
            print("subtask\t无")
            return
        print(f"subtask ({len(subs)}):")
        for s in subs:
            sdeps = ",".join(s.get("depends_on", [])) or "-"
            print(f"  {s['sid']}\t{s['status']}\t{_sub_pct(s)}%\t{s['name']}\t依赖:{sdeps}")

    def _brief(self, t: dict[str, Any]) -> dict[str, Any]:
        # 压缩任务摘要 (exec 取未完成任务用, 省 token): 仅调度所需字段, 不含全量 subtask 明细。
        # subs 数组固定序 [已完成, 运行中, 待处理, 失败]; ready = 该 就绪 task 前置全 done (可 start)。
        subs = t.get("subtasks", [])
        cnt = [0, 0, 0, 0]
        idx: dict[str, int] = {SS_DONE: 0, SS_RUNNING: 1, SS_PENDING: 2, SS_FAILED: 3}
        for s in subs:
            i = idx.get(s["status"])
            if i is not None:
                cnt[i] += 1
        pct = _task_pct(t)
        ready = t["status"] == S_READY and not any(
            self.ws._dep_unfinished(d) for d in t.get("deps", []))
        wt_shown = self.ws._wt_shown()
        return {"id": t["id"], "status": t["status"], "name": t.get("name", ""),
                "desc": t.get("desc", ""), "deps": t.get("deps", []),
                "repos": t.get("repos", []),
                "worktree": (t.get("worktree") or None) if wt_shown else None,
                "worktrees": [{"repo": w["repo"], "wt": w["wt"]} for w in worktrees_of(t)] if wt_shown else [],
                "pct": pct, "subs": cnt, "ready": ready}

    def list_(self, a: argparse.Namespace) -> None:
        tasks = self.ws.store.all_tasks()
        st = (getattr(a, "status", None) or "").strip()
        if st:
            if st in ("open", "unfinished", "未完成"):
                tasks = [t for t in tasks if t["status"] != S_DONE]
            else:
                wanted = {_STATUS_ALIAS.get(x.strip(), x.strip()) for x in st.split(",")}
                bad = wanted - {S_PENDING, S_READY, S_ACTIVE, S_CHECK, S_DONE}
                if bad:
                    raise SkeinError(
                        f"未知 status: {', '.join(sorted(bad))} — 可选 "
                        f"待处理/就绪/进行中/检查中/已完成 (或 pending/ready/active/check/done), open=全部未完成")
                tasks = [t for t in tasks if t["status"] in wanted]
        if getattr(a, "json", False):
            print(json.dumps([self._brief(t) for t in tasks],
                             ensure_ascii=False, separators=(",", ":")))
            return
        for t in tasks:
            print(f"{t['id']}\t{t['status']}\t{t['name']}")
