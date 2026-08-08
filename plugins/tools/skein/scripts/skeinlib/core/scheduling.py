"""`Scheduler` — subtask DAG 调度: 谁就绪、谁先派、认领即占槽。

## 两级调度
`subtask claim <tid>` 是单 task 内的就绪批; `claim exec` 是**全局跨 task** 的就绪批。
`claim` 不传 phase 时按 exec + check 同时预览/认领, 供主循环一次取两池状态。
所有可调度 task 的 ready subtask 合池竞争同一个 `pools.work`。两者共用 `_crit_weight`
关键路径权重排序: 最长下游链先派, 最小化 makespan。

## 为什么还拿着 Lifecycle
`claim check` 的第二路 (检查中 task 全 subtask done) 要把 task 收进「收尾中」, 走的是
`Lifecycle.finishing` (占 gate 槽) —— 复用同一条门, 不在这里另起一份校验。
`confirm` 吸收原 `start` 后, task 一旦过人审就直接进「进行中」, 不再有「就绪」态需要
subtask 认领时**就地启动**, 故这里不再需要 `Lifecycle._start_task` 那条路。
"""
from __future__ import annotations

import argparse
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from skeinlib.core.workspace import Workspace

from skeinlib.infra.worktree import workdir_for
from skeinlib.task.dag import _crit_weight, _split, _split_semi, _sub_estimate_sum, _sub_pct
from skeinlib.utils.errors import SkeinError
from skeinlib.task.model import (SubtaskStatus, SubtaskPhase, TaskStatus, PRIORITY_RANK, PRIORITY_DEFAULT,
                                 STATUS_ACTIVE,
                                 ESTIMATE_HINT, parse_hours, now)
from skeinlib.task import timeline as _timeline
from skeinlib.task.timeline import fmt_ts as _fmt_ts

from typing import TYPE_CHECKING as _TC

if _TC:
    from skeinlib.core.lifecycle import Lifecycle

# work 池出线打分 (design.md §4) —— 常数放模块级不进 config: 三个可调旋钮 = 三个没人知道
# 该填什么的旋钮, 真需要调再说。关键路径权重占绝对主导 (W_CRIT 远大于其余两项), 保证这套打分
# 在 p3 (task 优先级) 之下退化为原本的「关键路径优先, 同权重按登记序」——不破坏零回归。
# W_WAIT 让等待够久的活能翻盘 (防饿死); W_EXEC 是「软优先」而非硬抢占: exec 同分先走, 但等待
# 时长差超过一个 W_EXEC (=1 小时等价分) 时 research 能反超, 不会被无限期饿死。
_W_CRIT = 100.0
_W_WAIT = 1.0
_W_EXEC = 1.0


def _dispatch_hints(claimed: list[dict[str, Any]] | None = None,
                    checked: list[str] | None = None,
                    finishing: list[str] | None = None,
                    tasks: dict[str, dict[str, Any]] | None = None,
                    root: Any = None) -> list[dict[str, Any]]:
    """claim 认领了什么 → main 该派哪个 agent。"""
    hints: list[dict[str, Any]] = []
    for c in claimed or []:
        agent = ("skein:skein-researcher" if c.get("phase") == SubtaskPhase.RESEARCH
                 else "skein:skein-executor")
        hint = {"agent": agent, "tid": c["tid"], "sid": c["sid"], "why": "执行该 subtask"}
        if tasks:
            t = tasks[c["tid"]]
            repo = c.get("repo")
            if repo is None and len(t.get("worktrees") or []) > 1:
                hint["mismatch"] = "multi_repo_subtask_missing_repo"
            else:
                try:
                    hint["workdir"] = workdir_for(t, repo, root)
                except SkeinError as e:
                    hint["mismatch"] = "invalid_workdir"
                    hint["error"] = str(e)
                if repo is not None:
                    hint["repo"] = repo
        hints.append(hint)
    for tid in checked or []:
        hint: dict[str, Any] = {
            "agent": "skein:skein-checker", "tid": tid, "why": "验收该 task"
        }
        if tasks:
            t = tasks[tid]
            wts = t.get("worktrees") or []
            if len(wts) > 1:
                hint["workdirs"] = [workdir_for(t, w.get("repo"), root) for w in wts]
            else:
                hint["workdir"] = workdir_for(t, root=root)
        hints.append(hint)
    for tid in finishing or []:
        hint = {"agent": "skein:skein-finisher", "tid": tid, "why": "收尾合并该 task"}
        if tasks:
            hint["workdir"] = str(root or ".")
        hints.append(hint)
    return hints


def _report_mismatches(ws: "Workspace") -> list[dict[str, str]]:
    """报告文件已落盘但 subtask 未收尾，供 main 重派或介入。"""
    mismatches: list[dict[str, str]] = []
    for t in ws.store.all_tasks():
        if t.get("status") != TaskStatus.RESEARCH:
            continue
        report_dir = ws.tasks / t["id"] / "research"
        if not report_dir.is_dir():
            continue
        for s in t.get("subtasks", []):
            report = report_dir / f"{s['sid']}.md"
            if (s.get("phase") == SubtaskPhase.RESEARCH
                    and s.get("status") in (SubtaskStatus.PENDING, SubtaskStatus.RUNNING)
                    and report.is_file()):
                mismatches.append({"tid": t["id"], "sid": s["sid"],
                                   "reason": "research_report_exists_subtask_not_finished"})
    return mismatches


def _score(s: dict[str, Any], crit_val: int) -> float:
    """打分 = 关键路径权重×W_CRIT + 等待小时数×W_WAIT + (exec ? W_EXEC : 0)。"""
    wait_h = (now() - (s.get("created") or now())) / 3600.0
    exec_bonus = _W_EXEC if s.get("phase", SubtaskPhase.EXEC) == SubtaskPhase.EXEC else 0.0
    return crit_val * _W_CRIT + wait_h * _W_WAIT + exec_bonus


class Scheduler:
    """subtask DAG 就绪判定 + 认领。"""

    def __init__(self, ws: "Workspace", lifecycle: "Lifecycle") -> None:
        self.ws = ws
        self.lifecycle = lifecycle

    def _ready(self, t: dict[str, Any]) -> list[dict[str, Any]]:
        """就绪批: pending + 依赖全 done, 按打分降序排序后截到空闲槽位 (见 _score:
        关键路径优先 = 最长下游链先派, 最小化 makespan; 并行只看 depends_on DAG, 无写文件冲突自算;
        同分按登记序稳定)。"""
        subs = t.get("subtasks", [])
        done = {s["sid"] for s in subs if s["status"] == SubtaskStatus.DONE}
        running = [s for s in subs if s["status"] == SubtaskStatus.RUNNING]
        slots = self.ws.config()["pools"]["work"] - len(running)
        if slots <= 0:
            return []  # 并发满 → 阻塞
        crit = _crit_weight(subs)
        cand = [(i, s) for i, s in enumerate(subs)
                if s["status"] == SubtaskStatus.PENDING
                and all(d in done for d in s.get("depends_on", []))]
        # 打分降序, 同分按登记序稳定 (i 升序)
        cand.sort(key=lambda p: (-_score(p[1], crit.get(p[1]["sid"], 0)), p[0]))
        return [s for _, s in cand[:slots]]

    def _schedulable(self) -> list[dict[str, Any]]:
        """可被调度的 task: 全部 active 态 (进行中/调研中/收尾中), 按登记序。

        `confirm` 吸收原 `start` 后, task 一过人审门就直接进「进行中」并建好 worktree ——
        不再有「就绪但未启动」的中间态需要在这里补一次自动启动。
        """
        return self.ws.store.active()

    def _global_ready(self) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        """全局跨 task 就绪批: 所有**可调度** task (进行中 + 调研中 + 收尾中) 的 ready subtask
        合池, 按 (优先级降序, 打分降序, task 登记序, subtask 登记序) 排序, 截到全局 work 池
        (`pools.work`) - 全局 running 槽。优先级权重高于打分 (用户裁定: 标了紧急就真的先跑,
        代价是关键路径优化被冲淡)。依赖未满足的不入候选池 (见下方过滤), 优先级再高也不越过依赖。
        打分本身见 `_score` (关键路径×W_CRIT + 等待小时×W_WAIT + exec 加分 W_EXEC) —— W_CRIT
        远大于其余两项, 同优先级档内退化为「关键路径优先, 全同分按登记序」, 与打分引入前零回归。
        返回 [(task_obj, subtask_obj), ...]。"""
        tasks = self._schedulable()
        global_running = sum(
            1 for t in tasks for s in t.get("subtasks", []) if s["status"] == SubtaskStatus.RUNNING)
        slots = self.ws.config()["pools"]["work"] - global_running
        if slots <= 0:
            return []
        cand: list[tuple[dict[str, Any], dict[str, Any], int, int, float, int]] = []
        for ti, t in enumerate(tasks):
            subs = t.get("subtasks", [])
            done = {s["sid"] for s in subs if s["status"] == SubtaskStatus.DONE}
            crit = _crit_weight(subs)
            prio = PRIORITY_RANK.get(t.get("priority") or PRIORITY_DEFAULT, PRIORITY_RANK[PRIORITY_DEFAULT])
            for i, s in enumerate(subs):
                if s["status"] != SubtaskStatus.PENDING:
                    continue
                if not all(d in done for d in s.get("depends_on", [])):
                    continue  # 依赖未全 done 不入池 (依赖硬优先, 优先级不越过)
                cand.append((t, s, ti, i, _score(s, crit.get(s["sid"], 0)), prio))
        # 优先级降序 → 打分降序 → task 登记序 → subtask 登记序 (active task 也按优先级排,
        # 不再"同级不分"; 全同分时首项相等, 退化为改动前的顺序 → 零回归)
        cand.sort(key=lambda x: (-x[5], -x[4], x[2], x[3]))
        return [(c[0], c[1]) for c in cand[:slots]]

    def claim(self, a: argparse.Namespace) -> dict[str, Any]:
        """全局跨 task 认领批, 按 phase 分流:
        - exec: 所有可调度 task 的 ready subtask 合池竞争 pools.work 槽 → 整批标 running (旧 claim 行为)
        - check: 进行中 task 全 subtask done → 检查中; 检查中 task 全 subtask done 且 check 全绿 → 已完成 (finish)
        `--dry-run`: 只读预览, 不改状态。"""
        phase = getattr(a, "phase", None)
        if getattr(a, "dry_run", False):
            data: dict[str, Any] = {"phase": phase or "all", "dry_run": True}
            if phase in (None, "exec"):
                data["exec"] = self._claim_exec_preview(a)
            if phase in (None, "check"):
                data["check"] = self._claim_check_preview()
            return data
        results: dict[str, Any] = {}
        if phase is None:
            results["exec"] = self._claim_exec(a)
            results["check"] = self._claim_check(a)
        elif phase == "exec":
            return self._claim_exec(a)
        elif phase == "check":
            return self._claim_check(a)
        return results

    def _empty_batch_info(self) -> dict[str, Any]:
        """work 池空批原因 —— 满槽/无待处理/依赖未完成三种成因分开报。"""
        tasks = self._schedulable()
        grun = sum(1 for t in tasks for s in t.get("subtasks", []) if s["status"] == SubtaskStatus.RUNNING)
        gpend = sum(1 for t in tasks for s in t.get("subtasks", []) if s["status"] == SubtaskStatus.PENDING)
        mp = self.ws.config()["pools"]["work"]
        info: dict[str, Any] = {"running": grun, "capacity": mp, "pending": gpend}
        if grun >= mp:
            info.update({"reason": "work_pool_full", "message": "work 池已满 — 先等一个 subtask done 释放槽"})
        elif gpend == 0:
            info.update({"reason": "no_pending_subtask", "message": "无待处理 subtask"})
        else:
            info.update({"reason": "dependencies_blocked", "message": "待处理 subtask 的依赖未全部完成"})
        return info

    def _empty_batch_msg(self) -> str:
        info = self._empty_batch_info()
        if info["reason"] == "work_pool_full":
            return f"work 池已满 (running {info['running']}/{info['capacity']}) — 先等一个 subtask done 释放槽"
        if info["reason"] == "no_pending_subtask":
            return f"无待处理 subtask (work 池 running {info['running']}/{info['capacity']})"
        return (f"待处理 subtask 的依赖未全部完成 (work 池 running {info['running']}/{info['capacity']}, "
                f"pending: {info['pending']})")

    def _claim_exec_preview(self, a: argparse.Namespace) -> dict[str, Any]:
        batch = self._global_ready()
        task_filter = getattr(a, "task", None)
        if task_filter:
            batch = [(t, s) for t, s in batch if t["id"] == task_filter]
        items = []
        mismatches: list[dict[str, str]] = []
        for t, s in batch:
            item = {
                "task": t["id"],
                "subtask": s["sid"],
                "name": s["name"],
                "phase": s.get("phase", SubtaskPhase.EXEC),
                "repo": s.get("repo"),
                "skills": s.get("skills", []),
                "acceptance": s.get("acceptance", []),
            }
            try:
                item["workdir"] = workdir_for(t, s.get("repo"), self.ws.root)
            except SkeinError as e:
                item["mismatch"] = "invalid_workdir"
                item["error"] = str(e)
                mismatches.append({"tid": t["id"], "sid": s["sid"],
                                   "reason": "invalid_workdir", "error": str(e)})
            items.append(item)
        data: dict[str, Any] = {
            "ready": items,
            "count": len(items),
            "task_filter": task_filter,
            "claim_command": "skein claim exec",
            "single_claim_command": "skein subtask start <tid> <sid>",
            "mismatches": mismatches + _report_mismatches(self.ws),
        }
        if not items:
            data["empty"] = {"reason": "task_filter_no_ready", "task": task_filter} if task_filter else self._empty_batch_info()
        return data

    def _claim_exec(self, a: argparse.Namespace) -> dict[str, Any]:
        """exec 认领: ready subtask → running (与旧 claim 行为一致)。"""
        batch = self._global_ready()
        # --task 过滤: 只保留指定 task 的 subtask
        task_filter = getattr(a, "task", None)
        if task_filter:
            batch = [(t, s) for t, s in batch if t["id"] == task_filter]
        if getattr(a, "dry_run", False):
            return self._claim_exec_preview(a)
        if not batch:
            return {"claimed": [], "count": 0,
                    "reason": "task_filter_no_ready" if task_filter else self._empty_batch_info()}
        # 按 task 分组认领 (task 已全在 active 态, 无需就地启动)。
        by_tid: dict[str, list[str]] = {}
        order: list[str] = []
        for t, s in batch:
            if t["id"] not in by_tid:
                by_tid[t["id"]] = []
                order.append(t["id"])
            by_tid[t["id"]].append(s["sid"])
        claimed: list[dict[str, Any]] = []
        for tid in order:
            t = next(x for x, _ in batch if x["id"] == tid)
            subs = {s["sid"]: s for s in t.get("subtasks", [])}
            for sid in by_tid[tid]:
                s = subs[sid]
                s["status"] = SubtaskStatus.RUNNING
                if not s.get("started"):
                    s["started"] = now()  # exec 时刻 (首次认领, 重认领不覆盖)
                _timeline.append(t, "subtask", SubtaskStatus.RUNNING, sid=sid)
                claimed.append({"tid": tid, "sid": sid, "name": s["name"],
                                "phase": s.get("phase", SubtaskPhase.EXEC),
                                "repo": s.get("repo"),
                                "skills": s.get("skills", []),
                                "acceptance": s.get("acceptance", [])})
            self.ws.store.save(t)
        tasks = {t["id"]: t for t in self.ws.store.all_tasks()}
        return {"claimed": claimed, "count": len(claimed),
                "next": _dispatch_hints(claimed=claimed, tasks=tasks, root=self.ws.root),
                "mismatches": _report_mismatches(self.ws)}

    def _check_candidates(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        to_check: list[dict[str, Any]] = []
        to_finishing: list[dict[str, Any]] = []
        # 不能用 self.ws.store.active(): STATUS_ACTIVE = {进行中,调研中,收尾中} 不含「检查中」
        # (model.py:22) —— 用它会让下面的「检查中→收尾中」这一路永远遍历不到, 变成死代码。
        all_tasks = self.ws.store.all_tasks()
        for t in all_tasks:
            if t["status"] not in (TaskStatus.ACTIVE, TaskStatus.CHECK):
                continue
            if t.get("kind") == "supertask":
                # supertask 聚合层无自身 subtask, 就绪门换成「全部 child task done」(与 finish
                # 聚合归档门 lifecycle.py:452 同一套 parent==tid 判定, 只是提前到 check 这关)。
                children = [c for c in all_tasks if c.get("parent") == t["id"]]
                if not children or not all(c["status"] == TaskStatus.DONE for c in children):
                    continue
            else:
                subs = t.get("subtasks", [])
                if not subs:
                    continue
                if not all(s["status"] == SubtaskStatus.DONE for s in subs):
                    continue
            if t["status"] == TaskStatus.ACTIVE:
                to_check.append(t)
            elif t["status"] == TaskStatus.CHECK:
                # 检查中 + 全 done: 可收尾 (验收是否全绿由 skein-checker 保证, 这里只看状态)
                to_finishing.append(t)
        return to_check, to_finishing

    def _claim_check_preview(self) -> dict[str, Any]:
        to_check, to_finishing = self._check_candidates()
        data: dict[str, Any] = {
            "to_check": [{"task": t["id"], "name": t["name"], "next_status": TaskStatus.CHECK}
                         for t in to_check],
            "to_finishing": [{"task": t["id"], "name": t["name"], "next_status": TaskStatus.FINISHING}
                             for t in to_finishing],
            "check_count": len(to_check),
            "finishing_count": len(to_finishing),
            "claim_command": "skein claim check",
        }
        if not to_check and not to_finishing:
            data["empty"] = {"reason": "no_check_or_finishing_ready", "message": "进行中 task 须全 subtask done 才认领"}
        return data

    def _claim_check(self, a: argparse.Namespace) -> dict[str, Any]:
        """check 认领: 两路合并 —
        1. 进行中 task 全 subtask done → 检查中 (交给 skein-checker 验收)
        2. 检查中 task 全 subtask done → 收尾中 (finishing, 占 gate 槽; main 收到后派 skein-finisher 完成 finish)
        --dry-run 只读预览。"""
        to_check, to_finishing = self._check_candidates()
        dry = getattr(a, "dry_run", False)
        if not to_check and not to_finishing:
            return {"checked": [], "finishing": [], "errors": [],
                    "empty": {"reason": "no_check_or_finishing_ready",
                              "message": "进行中 task 须全 subtask done 才认领"}}
        if dry:
            return self._claim_check_preview()
        # 执行认领: 先 check 后 finishing (finishing 的 gate 槽校验依赖 check 已就位)
        checked: list[str] = []
        errors: list[dict[str, str]] = []
        for t in to_check:
            try:
                self.lifecycle.check(argparse.Namespace(id=t["id"]))  # 走同一道门, 带 stage hooks
                checked.append(t["id"])
            except SkeinError as e:
                errors.append({"tid": t["id"], "action": "check", "error": str(e)})
        # 收尾路调 lifecycle.finishing (占 gate 槽; gate 满则该 task 留检查中, 下次 claim 重试)
        finishing: list[str] = []
        for t in to_finishing:
            try:
                self.lifecycle.finishing(argparse.Namespace(id=t["id"]))
                finishing.append(t["id"])
            except SkeinError as e:
                errors.append({"tid": t["id"], "action": "finishing", "error": str(e)})
        tasks = {t["id"]: t for t in self.ws.store.all_tasks()}
        result: dict[str, Any] = {"checked": checked, "finishing": finishing,
                                  "next": _dispatch_hints(checked=checked, finishing=finishing,
                                                           tasks=tasks, root=self.ws.root),
                                  "mismatches": _report_mismatches(self.ws)}
        if errors:
            result["errors"] = errors
        return result

    def flow(self, a: argparse.Namespace) -> dict[str, Any]:
        """执行一次调度 tick：认领 exec/check，并返回 Agent 派发提示。"""
        result = self.claim(argparse.Namespace(
            phase=None,
            task=getattr(a, "task", None),
            dry_run=getattr(a, "dry_run", False),
        ))
        return {
            "action": "flow run",
            "dry_run": getattr(a, "dry_run", False),
            "result": result,
        }

    def subtask(self, a: argparse.Namespace) -> dict[str, Any]:
        if a.action == "add":
            t = self.ws.store.load(a.tid)
            subs = t.setdefault("subtasks", [])
            if any(s["sid"] == a.sid for s in subs):
                raise SkeinError(f"subtask 已存在: {a.tid}/{a.sid}")
            try:
                est = parse_hours(a.estimate)
            except (TypeError, ValueError):
                raise SkeinError(f"subtask 预计工时非法: {a.estimate!r} — {ESTIMATE_HINT}")
            if est <= 0:
                raise SkeinError(f"subtask 预计工时须为正数: {est}")
            repo = (getattr(a, "repo", None) or "").strip() or None
            declared_repos = t.get("repos") or []
            if repo is not None and repo not in declared_repos:
                raise SkeinError(f"{a.tid} 未声明 repo={repo!r} — 先用 `skein task repos {a.tid} --set ...` 声明")
            if repo is None and len(declared_repos) > 1:
                raise SkeinError(f"{a.tid} 有多个 repo — subtask add 必须声明 --repo")
            subs.append({
                "sid": a.sid, "name": a.name, "desc": a.desc,
                "estimate": est,  # 预计工时(小时), add 必填; task estimate 须 ≥ Σ 本字段
                "depends_on": _split(a.deps),
                "acceptance": _split_semi(a.check),  # 验收标准 checklist (字符串数组)
                "acceptance_done": [],  # 已通过验收标准序号(1-based); 完成百分比 = len/len(acceptance)
                "status": SubtaskStatus.PENDING,
                "phase": getattr(a, "phase", None) or SubtaskPhase.EXEC,  # exec(默认) | research
                "repo": repo,
                "skills": _split(a.skills),  # 关联 skills (0-n)
                "created": now(),   # 创建时刻
                "started": None,    # exec 时刻 (claim/start →运行中 时置)
                "finished": None,   # 完成时刻 (done 时置)
            })
            self.ws.store.save(t)  # _save 已渲染子任务看板
            return {"tid": a.tid, "sid": a.sid, "estimate": est,
                    "total": len(subs), "subtask_sum": _sub_estimate_sum(t)}
        if a.action == "list":
            t = self.ws.store.load(a.tid)
            subs = t.get("subtasks", [])
            return {"tid": a.tid, "subtasks": [{"sid": s["sid"], "status": s["status"],
                    "name": s["name"], "pct": _sub_pct(s),
                    "estimate": s.get("estimate"),
                    "repo": s.get("repo"),
                    "depends_on": s.get("depends_on", []),
                    "acceptance": s.get("acceptance", []),
                    "skills": s.get("skills", [])} for s in subs]}
        if a.action == "show":
            t = self.ws.store.load(a.tid)
            s = self.ws._sub(t, a.sid)
            return {"tid": a.tid, "subtask": s}
        if a.action in ("ready", "claim"):
            t = self.ws.store.load(a.tid)
            batch = self._ready(t)
            if not batch:
                run = [s["sid"] for s in t.get("subtasks", []) if s["status"] == SubtaskStatus.RUNNING]
                mp = self.ws.config()["pools"]["work"]
                reason = "work_pool_full" if len(run) >= mp else "dependencies_blocked"
                return {"ready": [], "reason": reason, "running": len(run), "capacity": mp}
            if a.action == "claim":
                # 一次性认领: 就绪批整体标 running, 免 main 逐个 start (少一轮往返 + 无竞态窗口)
                for s in batch:
                    s["status"] = SubtaskStatus.RUNNING
                    if not s.get("started"):
                        s["started"] = now()  # exec 时刻 (首次认领, 重认领不覆盖)
                    _timeline.append(t, "subtask", SubtaskStatus.RUNNING, sid=s["sid"])
                self.ws.store.save(t)  # _save 已渲染子任务看板
            return {"tid": a.tid, "action": a.action,
                    "claimed" if a.action == "claim" else "ready": [
                        {"sid": s["sid"], "name": s["name"],
                         "phase": s.get("phase", SubtaskPhase.EXEC),
                         "repo": s.get("repo"),
                         "workdir": workdir_for(t, s.get("repo"), self.ws.root),
                         "skills": s.get("skills", []), "acceptance": s.get("acceptance", [])}
                        for s in batch],
                    "next": _dispatch_hints(
                        claimed=[{"tid": a.tid, "sid": s["sid"],
                                  "phase": s.get("phase", SubtaskPhase.EXEC),
                                  "repo": s.get("repo")} for s in batch],
                        tasks={a.tid: t}, root=self.ws.root
                    ) if a.action == "claim" else [],
                    "mismatches": _report_mismatches(self.ws)}
        # start / done / fail / check 均针对单 sid
        t = self.ws.store.load(a.tid)
        s = self.ws._sub(t, a.sid)
        if a.action == "start":
            # task 必须先进可调度态 —— 否则 `subtask start` 就是一条绕过 confirm 人审门的暗道:
            # pending task 的 subtask 照样能 start→done 把活全干完, 干完才发现 task 卡在 pending
            # 进不了 check ("状态 pending, 只有进行中 task 能进检查"), 人审等于没发生。
            # claim 路径走 _schedulable() 早就筛过状态, 只有这条单点路径漏了。
            if t["status"] not in STATUS_ACTIVE:
                raise SkeinError(
                    f"{a.tid} 状态 {t['status']}, 不能 start subtask — "
                    f"先 `skein task confirm {a.tid}` 过人审门进「进行中」"
                    f"(调研类 subtask 走 `skein task research {a.tid}`)")
            if t["status"] == TaskStatus.RESEARCH and s.get("phase") != SubtaskPhase.RESEARCH:
                raise SkeinError(
                    f"{a.tid} 调研中, 只能 start phase=research 的 subtask — "
                    f"先 `skein task plan {a.tid}` 收敛回规划再 confirm")
            if s["status"] not in (SubtaskStatus.PENDING, SubtaskStatus.FAILED):
                raise SkeinError(f"{a.sid} 状态 {s['status']}, 只能 start 待处理/失败")
            done = {x["sid"] for x in t["subtasks"] if x["status"] == SubtaskStatus.DONE}
            undone = [d for d in s.get("depends_on", []) if d not in done]
            if undone:
                raise SkeinError(f"依赖未完成: {', '.join(undone)} — 先 done 它们")
            run = [x for x in t["subtasks"] if x["status"] == SubtaskStatus.RUNNING]
            if len(run) >= self.ws.config()["pools"]["work"]:
                raise SkeinError(f"并发已满 ({len(run)}) — 先 done 一个再 start")
            self.ws._stage_hooks("subtask.start", "before", self.ws._hook_ctx(a.tid, a.sid, t=t))
            s["status"] = SubtaskStatus.RUNNING
            if not s.get("started"):
                s["started"] = now()  # exec 时刻 (首次 start, 重启不覆盖)
            _timeline.append(t, "subtask", SubtaskStatus.RUNNING, sid=a.sid)
        elif a.action == "check":
            crit = s.get("acceptance", [])
            val = (a.passed or "").strip()
            if val == "all":
                idx = list(range(1, len(crit) + 1))
            elif val in ("none", ""):
                idx = []
            else:
                idx = sorted({int(x) for x in _split(val)})
                bad = [i for i in idx if i < 1 or i > len(crit)]
                if bad:
                    raise SkeinError(f"验收序号越界: {bad} (共 {len(crit)} 条)")
            s["acceptance_done"] = idx
            self.ws.store.save(t)  # _save 已渲染子任务看板
            return {"tid": a.tid, "sid": a.sid, "accepted": len(idx),
                    "total": len(crit), "pct": _sub_pct(s)}
        elif a.action == "done":
            self.ws._stage_hooks("subtask.done", "before", self.ws._hook_ctx(a.tid, a.sid, t=t))
            s["status"] = SubtaskStatus.DONE
            s["finished"] = now()  # 完成时刻
            s["acceptance_done"] = list(range(1, len(s.get("acceptance", [])) + 1))  # 完成即全过 → 100%
            _timeline.append(t, "subtask", SubtaskStatus.DONE, sid=a.sid)
        elif a.action == "fail":
            self.ws._stage_hooks("subtask.fail", "before", self.ws._hook_ctx(a.tid, a.sid, t=t))
            s["status"] = SubtaskStatus.FAILED
            s["finished"] = now()  # 失败时刻 (与 done 对称)
            if a.note:
                s["note"] = a.note  # 失败备注 (运行时, 非 planning schema)
            _timeline.append(t, "subtask", SubtaskStatus.FAILED, sid=a.sid, note=a.note or "")
        self.ws.store.save(t)  # _save 已渲染子任务看板
        if a.action in ("start", "done", "fail"):
            self.ws._stage_hooks(f"subtask.{a.action}", "after", self.ws._hook_ctx(a.tid, a.sid, t=t))
        return {"tid": a.tid, "sid": a.sid, "status": s["status"]}
