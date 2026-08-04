"""调度与进度的纯函数 — 无 self / 无 IO / 无落盘, 给定 dict 就出结果。

`_crit_weight` 决定 subtask 派发顺序 (关键路径优先, 最小化 makespan), `_pending_queue` 决定
task 级就绪队列。这层不碰文件, 所以能直接单测, 不必起子进程。
"""
from __future__ import annotations

from typing import Any, Optional

from skeinlib.task.model import (PHASE_OF, SubtaskStatus, STATUS_ACTIVE, TaskStatus)

def _split(s: Optional[str]) -> list[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()]
def _split_semi(s: Optional[str]) -> list[str]:
    # 验收 checklist 用分号分隔 (条目内可含逗号)
    return [x.strip() for x in (s or "").split(";") if x.strip()]
def _sub_estimate_sum(t: dict[str, Any]) -> float:
    # Σ subtask 预计工时 (小时)。老数据无 estimate 字段的按 0 计, 不阻断历史 task。
    vals = [s.get("estimate") for s in t.get("subtasks") or []]
    return round(sum(v for v in vals if isinstance(v, (int, float)) and v > 0), 2)
_SUB_PCT_RANGE = {SubtaskStatus.PENDING: (0, 5), SubtaskStatus.RUNNING: (10, 90), SubtaskStatus.FAILED: (10, 90)}
# ponytail: 失败与运行同区间 — 用户裁定冻结在失败前进度, 重试不回跳。
_TASK_PCT_RANGE = {TaskStatus.PENDING: (0, 5), TaskStatus.RESEARCH: (5, 10), TaskStatus.ACTIVE: (10, 85),
                   TaskStatus.CHECK: (85, 95), TaskStatus.FINISHING: (95, 98)}

def _sub_pct(s: dict[str, Any]) -> int:
    # subtask 完成百分比 = 状态区间 + 验收线性插值 (done 强制 100; 无验收项取区间中点)。
    # 全用 floor (int()), 禁 round() — 防 banker's rounding 与前端 JS Math.floor 分歧。
    if s["status"] == SubtaskStatus.DONE:
        return 100
    lo, hi = _SUB_PCT_RANGE.get(s["status"], (0, 5))
    crit = s.get("acceptance", [])
    if crit:
        return int(lo + (hi - lo) * len(s.get("acceptance_done", [])) / len(crit))
    return (lo + hi) // 2
def _task_pct(t: dict[str, Any]) -> int:
    # task 进度 = 状态区间 + subtask 完成度均值线性插值 (done 强制 100; 无 subs 取区间中点)。
    st = t.get("status", "")
    if st == TaskStatus.DONE:
        return 100
    lo, hi = _TASK_PCT_RANGE.get(st, (0, 5))
    subs: list[dict[str, Any]] = t.get("subtasks", [])
    if subs:
        sub_avg = sum(_sub_pct(s) for s in subs) / len(subs)
        return int(lo + (hi - lo) * sub_avg / 100)
    return (lo + hi) // 2
def _task_stage(t: dict[str, Any]) -> str:
    # task 阶段标签 (plan/research/exec/check/finishing/done) 供 board card 渲染
    st = t.get("status", "")
    if st == TaskStatus.DONE:
        return "done"
    return PHASE_OF.get(st, "plan")  # 待处理→plan / 调研中→research / 进行中→exec / 检查中→check / 收尾中→finishing
def _crit_weight(subs: list[dict[str, Any]]) -> dict[str, int]:
    """纯拓扑深度: 每 subtask 的最长下游链长 (每步计 1, 不依赖 estimate)。
    权重大 = 越靠关键路径 (阻塞最多下游), 槽位紧张时优先派 → 最小化 makespan (总工期)。"""
    succ: dict[str, list[str]] = {}  # sid -> 直接下游 sid
    for s in subs:
        for d in s.get("depends_on", []):
            succ.setdefault(d, []).append(s["sid"])
    memo: dict[str, int] = {}

    def w(sid: str, seen: tuple[str, ...] = ()) -> int:
        if sid in memo:
            return memo[sid]
        if sid in seen:  # ponytail: 环保护 (DAG 校验兜底不该到这), 断链避免无限递归, 不缓存
            return 1
        r = 1 + max((w(c, seen + (sid,)) for c in succ.get(sid, [])), default=0)
        memo[sid] = r
        return r

    return {s["sid"]: w(s["sid"]) for s in subs}
def _pending_queue(tasks: list[dict[str, Any]], dep_unfinished: Any) -> list[dict[str, Any]]:
    """待执行 subtask 队列 (全部未完成 task, 同调度序): 每个 pending subtask 一条。
    排序 = task 调度序 (active 态(进行中/调研中/收尾中) > 阻塞前置的 pending, 同级按传入顺序)
    → task 内 (真就绪 > 关键路径权重降序 > 登记序)。
    真就绪 = task 处于 active 态且 subtask 依赖全 done (可立即派); 其余为排队中。"""
    q: list[dict[str, Any]] = []
    for ti, t in enumerate(tasks):
        if t["status"] not in (TaskStatus.PENDING, TaskStatus.RESEARCH, TaskStatus.ACTIVE, TaskStatus.CHECK, TaskStatus.FINISHING):
            continue  # 已完成/失败 task 跳过
        subs = t.get("subtasks", [])
        if not any(s["status"] == SubtaskStatus.PENDING for s in subs):
            continue
        active = t["status"] in STATUS_ACTIVE
        blocked = any(dep_unfinished(d) for d in t.get("deps", []))
        trank = 0 if active else (2 if blocked else 1)
        done = {s["sid"] for s in subs if s["status"] == SubtaskStatus.DONE}
        crit = _crit_weight(subs)
        for i, s in enumerate(subs):
            if s["status"] != SubtaskStatus.PENDING:
                continue
            ready = active and all(d in done for d in s.get("depends_on", []))
            q.append({
                "tid": t["id"], "sid": s["sid"], "name": s.get("name", s["sid"]),
                "ready": ready,
                "trank": trank, "ti": ti, "crit": crit.get(s["sid"], 0),
                "i": i,
                "desc": s.get("desc", ""), "status": s["status"],
                "depends_on": s.get("depends_on", []),
            })
    q.sort(key=lambda x: (x["trank"], x["ti"], not x["ready"], -x["crit"], x["i"]))
    return q

def detect_cycle(graph: dict[str, list[str]]) -> Optional[list[str]]:
    """三色 DFS 环检测 — 返回首个环路径 (节点序列含首尾) 或 None。
    纯函数, 给 lifecycle.deps 和 doctor 各调一份 (ADR 0003 G4 消除重复)。"""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph}
    stack: list[str] = []

    def _dfs(n: str) -> Optional[list[str]]:
        color[n] = GRAY
        stack.append(n)
        for m in graph.get(n, []):
            if m not in color:
                continue
            if color[m] == GRAY:
                return stack[stack.index(m):] + [m]
            if color[m] == WHITE:
                r = _dfs(m)
                if r:
                    return r
        color[n] = BLACK
        stack.pop()
        return None

    for n in graph:
        if color[n] == WHITE:
            r = _dfs(n)
            if r:
                return r
    return None
