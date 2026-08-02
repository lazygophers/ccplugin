"""`Scheduler` — subtask DAG 调度: 谁就绪、谁先派、认领即占槽。

## 两级调度
`subtask claim <tid>` 是单 task 内的就绪批; `claim exec` (无 tid) 是**全局跨 task** 的就绪批 ——
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
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from skeinlib.workspace import Workspace

from skeinlib.task.dag import _crit_weight, _split, _split_semi, _sub_estimate_sum, _sub_pct
from skeinlib.errors import SkeinError
from skeinlib.task.model import (SubtaskStatus, SubtaskPhase, TaskStatus, PRIORITY_RANK, PRIORITY_DEFAULT, now)
from skeinlib.views import _fmt_ts

from typing import TYPE_CHECKING as _TC

if _TC:
    from skeinlib.lifecycle import Lifecycle

# work 池出线打分 (design.md §4) —— 常数放模块级不进 config: 三个可调旋钮 = 三个没人知道
# 该填什么的旋钮, 真需要调再说。关键路径权重占绝对主导 (W_CRIT 远大于其余两项), 保证这套打分
# 在 p3 (task 优先级) 之下退化为原本的「关键路径优先, 同权重按登记序」——不破坏零回归。
# W_WAIT 让等待够久的活能翻盘 (防饿死); W_EXEC 是「软优先」而非硬抢占: exec 同分先走, 但等待
# 时长差超过一个 W_EXEC (=1 小时等价分) 时 research 能反超, 不会被无限期饿死。
_W_CRIT = 100.0
_W_WAIT = 1.0
_W_EXEC = 1.0


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

    def claim(self, a: argparse.Namespace) -> None:
        """全局跨 task 认领批, 按 phase 分流:
        - exec: 所有可调度 task 的 ready subtask 合池竞争 pools.work 槽 → 整批标 running (旧 claim 行为)
        - check: 进行中 task 全 subtask done → 检查中; 检查中 task 全 subtask done 且 check 全绿 → 已完成 (finish)
        `--dry-run`: 只读预览, 不改状态。"""
        phase = getattr(a, "phase", "exec")
        if phase == "exec":
            self._claim_exec(a)
        elif phase == "check":
            self._claim_check(a)

    def _empty_batch_msg(self) -> str:
        """work 池空批提示 —— 满槽/无待处理/依赖未完成三种成因分开报, 满槽明确指明「work 池」。"""
        tasks = self._schedulable()
        grun = sum(1 for t in tasks for s in t.get("subtasks", []) if s["status"] == SubtaskStatus.RUNNING)
        gpend = sum(1 for t in tasks for s in t.get("subtasks", []) if s["status"] == SubtaskStatus.PENDING)
        mp = self.ws.config()["pools"]["work"]
        if grun >= mp:
            return f"work 池已满 (running {grun}/{mp}) — 先等一个 subtask done 释放槽"
        if gpend == 0:
            return f"无待处理 subtask (work 池 running {grun}/{mp})"
        return f"待处理 subtask 的依赖未全部完成 (work 池 running {grun}/{mp}, pending: {gpend})"

    def _claim_exec(self, a: argparse.Namespace) -> None:
        """exec 认领: ready subtask → running (与旧 claim 行为一致)。"""
        batch = self._global_ready()
        # --task 过滤: 只保留指定 task 的 subtask
        task_filter = getattr(a, "task", None)
        if task_filter:
            batch = [(t, s) for t, s in batch if t["id"] == task_filter]
        if getattr(a, "dry_run", False):
            if not batch:
                if task_filter:
                    print(f"task {task_filter} 无就绪 subtask")
                else:
                    print(f"无全局就绪 subtask — {self._empty_batch_msg()}")
                return
            print("全局就绪批 (只读预览, 不改状态) — 决定执行后去掉 --dry-run 认领:")
            for t, s in batch:
                sk = ",".join(s.get("skills", [])) or "-"
                chk = "; ".join(s.get("acceptance", [])) or "-"
                print(f"{t['id']}/{s['sid']}\t{s['name']}\tskills: {sk}\t验收: {chk}")
            print("— 认领整批: `skein.py claim exec`  或只占单个: `skein.py subtask start <tid> <sid>`")
            return
        if not batch:
            if task_filter:
                print(f"task {task_filter} 无就绪 subtask")
            else:
                print(f"无全局就绪 subtask — {self._empty_batch_msg()}")
            return
        # 按 task 分组认领 (task 已全在 active 态, 无需就地启动)。
        by_tid: dict[str, list[str]] = {}
        order: list[str] = []
        for t, s in batch:
            if t["id"] not in by_tid:
                by_tid[t["id"]] = []
                order.append(t["id"])
            by_tid[t["id"]].append(s["sid"])
        claimed: list[tuple[str, dict[str, Any]]] = []
        for tid in order:
            t = next(x for x, _ in batch if x["id"] == tid)
            subs = {s["sid"]: s for s in t.get("subtasks", [])}
            for sid in by_tid[tid]:
                s = subs[sid]
                s["status"] = SubtaskStatus.RUNNING
                if not s.get("started"):
                    s["started"] = now()  # exec 时刻 (首次认领, 重认领不覆盖)
                claimed.append((tid, s))
            self.ws.store.save(t)
        print("已全局认领 (running) — main 逐个派 skein-executor（dispatch 只给 tid + sid + 工作目录）, 完成即 subtask done/fail:")
        for tid, s in claimed:
            sk = ",".join(s.get("skills", [])) or "-"
            chk = "; ".join(s.get("acceptance", [])) or "-"
            print(f"{tid}/{s['sid']}\t{s['name']}\tskills: {sk}\t验收: {chk}")

    def _claim_check(self, a: argparse.Namespace) -> None:
        """check 认领: 两路合并 —
        1. 进行中 task 全 subtask done → 检查中 (交给 skein-checker 验收)
        2. 检查中 task 全 subtask done → 收尾中 (finishing, 占 gate 槽; main 收到后派 skein-finisher 完成 finish)
        --dry-run 只读预览。"""
        to_check: list[dict[str, Any]] = []
        to_finishing: list[dict[str, Any]] = []
        # 不能用 self.ws.store.active(): STATUS_ACTIVE = {进行中,调研中,收尾中} 不含「检查中」
        # (model.py:22) —— 用它会让下面的「检查中→收尾中」这一路永远遍历不到, 变成死代码。
        for t in self.ws.store.all_tasks():
            if t["status"] not in (TaskStatus.ACTIVE, TaskStatus.CHECK):
                continue
            subs = t.get("subtasks", [])
            if not subs:
                continue
            all_done = all(s["status"] == SubtaskStatus.DONE for s in subs)
            if not all_done:
                continue
            if t["status"] == TaskStatus.ACTIVE:
                to_check.append(t)
            elif t["status"] == TaskStatus.CHECK:
                # 检查中 + 全 done: 可收尾 (验收是否全绿由 skein-checker 保证, 这里只看状态)
                to_finishing.append(t)
        dry = getattr(a, "dry_run", False)
        if not to_check and not to_finishing:
            print("无可认领的 check/finishing task — 进行中 task 须全 subtask done 才认领")
            return
        if dry:
            if to_check:
                print("待进检查 (只读预览, 不改状态) — 去掉 --dry-run 认领:")
                for t in to_check:
                    print(f"  {t['id']}\t{t['name']} → 检查中")
            if to_finishing:
                print("待收尾 (只读预览, 不改状态) — 去掉 --dry-run 认领:")
                for t in to_finishing:
                    print(f"  {t['id']}\t{t['name']} → 收尾中 (占 gate 槽)")
            return
        # 执行认领: 先 check 后 finishing (finishing 的 gate 槽校验依赖 check 已就位)
        claimed_check: list[str] = []
        for t in to_check:
            t["status"] = TaskStatus.CHECK
            t["checked"] = now()
            self.ws.store.save(t)
            claimed_check.append(t["id"])
        if claimed_check:
            self.ws.store.sync()
            print(f"已认领进检查 ({len(claimed_check)} task) — main 派 skein-checker 验收:")
            for tid in claimed_check:
                print(f"  {tid}")
        # 收尾路调 lifecycle.finishing (占 gate 槽; gate 满则该 task 留检查中, 下次 claim 重试)
        claimed_finishing: list[str] = []
        for t in to_finishing:
            try:
                self.lifecycle.finishing(argparse.Namespace(id=t["id"]))
                claimed_finishing.append(t["id"])
            except SkeinError as e:
                print(f"  {t['id']}: 收尾失败 — {e}")
        if claimed_finishing:
            print(f"已认领收尾 ({len(claimed_finishing)} task) — main 派 skein-finisher 完成 finish:")
            for tid in claimed_finishing:
                print(f"  {tid}")

    def subtask(self, a: argparse.Namespace) -> None:
        if a.action == "add":
            t = self.ws.store.load(a.tid)
            subs = t.setdefault("subtasks", [])
            if any(s["sid"] == a.sid for s in subs):
                raise SkeinError(f"subtask 已存在: {a.tid}/{a.sid}")
            try:
                est = float(a.estimate)
            except (TypeError, ValueError):
                raise SkeinError(f"subtask 预计工时须为数字(小时): {a.estimate!r}")
            if est <= 0:
                raise SkeinError(f"subtask 预计工时须为正数: {est}")
            subs.append({
                "sid": a.sid, "name": a.name, "desc": a.desc,
                "estimate": est,  # 预计工时(小时), add 必填; task estimate 须 ≥ Σ 本字段
                "depends_on": _split(a.deps),
                "acceptance": _split_semi(a.check),  # 验收标准 checklist (字符串数组)
                "acceptance_done": [],  # 已通过验收标准序号(1-based); 完成百分比 = len/len(acceptance)
                "status": SubtaskStatus.PENDING,
                "phase": getattr(a, "phase", None) or SubtaskPhase.EXEC,  # exec(默认) | research
                "skills": _split(a.skills),  # 关联 skills (0-n)
                "created": now(),   # 创建时刻
                "started": None,    # exec 时刻 (claim/start →运行中 时置)
                "finished": None,   # 完成时刻 (done 时置)
            })
            self.ws.store.save(t)  # _save 已渲染子任务看板
            print(f"{a.tid}/{a.sid} 已登记 ({est} h; 共 {len(subs)} subtask, "
                  f"合计 {_sub_estimate_sum(t)} h)")
            return
        if a.action == "list":
            t = self.ws.store.load(a.tid)
            subs = t.get("subtasks", [])
            if not subs:
                print("无 subtask")
                return
            for s in subs:
                deps = ",".join(s.get("depends_on", [])) or "-"
                chk = "; ".join(s.get("acceptance", [])) or "-"
                sk = ",".join(s.get("skills", [])) or "-"
                est_v = s.get("estimate")  # est_v 而非 est: 避免与本函数 add 分支的 est(float) 同名混型
                print(f"{s['sid']}\t{s['status']}\t{_sub_pct(s)}%\t{est_v if est_v else '-'}h\t{s['name']}"
                      f"\t依赖:{deps}\t验收:{chk}\tskills:{sk}")
            return
        if a.action == "show":
            t = self.ws.store.load(a.tid)
            s = self.ws._sub(t, a.sid)
            crit = s.get("acceptance", [])
            doneidx = set(s.get("acceptance_done", []))
            est_v = s.get("estimate")  # est_v 而非 est: 避免与本函数 add 分支的 est(float) 同名混型
            elapsed = None
            if s.get("started") and s.get("finished"):
                elapsed = round((s["finished"] - s["started"]) / 60, 1)  # 分钟
            print(f"sid: {s['sid']}")
            print(f"name: {s['name']}")
            print(f"desc: {s.get('desc') or '-'}")
            print(f"status: {s['status']}")
            print(f"estimate: {est_v if est_v else '-'} h")
            print(f"实际耗时: {elapsed if elapsed is not None else '-'} min")
            print(f"depends_on: {','.join(s.get('depends_on', [])) or '-'}")
            print(f"skills: {','.join(s.get('skills', [])) or '-'}")
            if crit:
                print("验收:")
                for i, c in enumerate(crit, 1):
                    mark = "x" if i in doneidx else " "
                    print(f"  [{mark}] {i}. {c}")
            else:
                print("验收: -")
            print(f"note: {s.get('note') or '-'}")
            print(f"created: {_fmt_ts(s.get('created'))}")
            print(f"started: {_fmt_ts(s.get('started'))}")
            print(f"finished: {_fmt_ts(s.get('finished'))}")
            return
        if a.action in ("ready", "claim"):
            t = self.ws.store.load(a.tid)
            batch = self._ready(t)
            if not batch:
                run = [s["sid"] for s in t.get("subtasks", []) if s["status"] == SubtaskStatus.RUNNING]
                pend = [s for s in t.get("subtasks", []) if s["status"] == SubtaskStatus.PENDING]
                mp = self.ws.config()["pools"]["work"]
                if len(run) >= mp:
                    print(f"无就绪 subtask — work 池已满 (running {len(run)}/{mp})")
                else:
                    print(f"无就绪 subtask (running: {','.join(run) or '-'}, "
                          f"pending: {len(pend)}) — 依赖未完成")
                return
            if a.action == "claim":
                # 一次性认领: 就绪批整体标 running, 免 main 逐个 start (少一轮往返 + 无竞态窗口)
                for s in batch:
                    s["status"] = SubtaskStatus.RUNNING
                    if not s.get("started"):
                        s["started"] = now()  # exec 时刻 (首次认领, 重认领不覆盖)
                self.ws.store.save(t)  # _save 已渲染子任务看板
                print("已认领 (running) — main 逐个派 skein-executor（dispatch 只给 tid + sid + 工作目录）, 完成即 subtask done/fail:")
            else:
                print("就绪 (只读预览, 认领用 `subtask claim`):")
            for s in batch:
                sk = ",".join(s.get("skills", [])) or "-"
                chk = "; ".join(s.get("acceptance", [])) or "-"
                print(f"{s['sid']}\t{s['name']}\tskills: {sk}\t验收: {chk}")
            return
        # start / done / fail 均针对单 sid
        t = self.ws.store.load(a.tid)
        s = self.ws._sub(t, a.sid)
        if a.action == "start":
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
            print(f"{a.tid}/{a.sid} 验收 {len(idx)}/{len(crit)} ({_sub_pct(s)}%)")
            return
        elif a.action == "done":
            self.ws._stage_hooks("subtask.done", "before", self.ws._hook_ctx(a.tid, a.sid, t=t))
            s["status"] = SubtaskStatus.DONE
            s["finished"] = now()  # 完成时刻
            s["acceptance_done"] = list(range(1, len(s.get("acceptance", [])) + 1))  # 完成即全过 → 100%
        elif a.action == "fail":
            self.ws._stage_hooks("subtask.fail", "before", self.ws._hook_ctx(a.tid, a.sid, t=t))
            s["status"] = SubtaskStatus.FAILED
            s["finished"] = now()  # 失败时刻 (与 done 对称)
            if a.note:
                s["note"] = a.note  # 失败备注 (运行时, 非 planning schema)
        self.ws.store.save(t)  # _save 已渲染子任务看板
        if a.action in ("start", "done", "fail"):
            self.ws._stage_hooks(f"subtask.{a.action}", "after", self.ws._hook_ctx(a.tid, a.sid, t=t))
        print(f"{a.tid}/{a.sid} → {s['status']}")
