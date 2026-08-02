"""看板 / webapp 视图层 — `Snapshot` 一次扫描, 各 `_view_*` 把它变成 dict。

`Snapshot` 是本层唯一输入契约: 六个视图共用同一份数据, 免每个视图各扫一遍目录。
`DataSource` Protocol 是 http 层的注入点 —— 生产喂真 Skein, 测试喂假对象, 两个 adapter。
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Callable, Optional, Protocol, cast

from skeinlib.dag import _pending_queue, _sub_pct, _task_pct, _task_stage
from skeinlib.model import (PRIORITY_DEFAULT, SS_DONE, SS_PENDING, SS_RUNNING, STATUS_ACTIVE,
                            STATUS_INFLIGHT, STATUS_ORDER, S_ACTIVE, S_CHECK, S_DONE,
                            S_FINISHING, S_PENDING, S_RESEARCH, now)
from skeinlib.worktree import git

class Snapshot:
    """一次目录扫描的 task/subtask 内存快照 — board 视图的统一输入。
    惰性: tasks(渲染源)/all_tasks(严格真值) 首次访问才扫盘并缓存; prd/design/task.json 按需读 (task_path/prd_path)。
    → task_detail 只碰路径不触发全量扫描 (旧行为), 其余视图访问 .tasks 时才实扫。
    dep_unfinished 由缓存态 O(1) 判定 (取代逐 dep 读盘)。构造经 Skein._snapshot(), 每请求一次。"""

    def __init__(self, *, proj: str, wt_shown: bool,
                 tasks_fn: Callable[[], list[dict[str, Any]]],
                 all_tasks_fn: Callable[[], list[dict[str, Any]]],
                 tasks_dir: Path, archive_dir: Path, spec_root: Path,
                 pool_work: int = 2, gate_active: int = 3) -> None:
        self.proj = proj
        self.wt_shown = wt_shown
        self.pool_work = pool_work  # work 池上限; 前端 ETA 按此折算并行墙钟
        self.gate_active = gate_active  # gate 池上限 (check+finishing task 并发)
        self._tasks_fn = tasks_fn      # _render_tasks(): 顶层索引 ∪ per-task 明细 (含幽灵骨架)
        self._all_fn = all_tasks_fn    # _all(): per-task 严格真值 (无幽灵骨架)
        self._tasks_dir = tasks_dir
        self.archive_dir = archive_dir
        self.spec_root = spec_root
        self._tasks_cache: Optional[list[dict[str, Any]]] = None
        self._all_cache: Optional[list[dict[str, Any]]] = None
        self._dep_index: Optional[tuple[set[str], dict[str, str], set[str]]] = None

    @property
    def tasks(self) -> list[dict[str, Any]]:
        if self._tasks_cache is None:
            self._tasks_cache = self._tasks_fn()
        return self._tasks_cache

    @property
    def all_tasks(self) -> list[dict[str, Any]]:
        if self._all_cache is None:
            self._all_cache = self._all_fn()
        return self._all_cache

    @property
    def active(self) -> list[dict[str, Any]]:
        return [t for t in self.all_tasks if t["status"] in STATUS_ACTIVE]

    def dep_unfinished(self, dep: str) -> bool:
        # 等价 Skein._dep_unfinished: 归档→完成; 未知(无 per-task 目录)→不阻塞; 否则 status!=已完成
        if self._dep_index is None:
            all_ids = {t["id"] for t in self.all_tasks}
            status_by_id = {t["id"]: t["status"] for t in self.all_tasks}
            archived_ids = ({p.name for p in self.archive_dir.glob("*/*/*")}
                            if self.archive_dir.exists() else set())
            self._dep_index = (all_ids, status_by_id, archived_ids)
        all_ids, status_by_id, archived_ids = self._dep_index
        if dep in archived_ids:
            return False
        if dep not in all_ids:
            return False
        return status_by_id[dep] != S_DONE

    def task_path(self, tid: str) -> Path:
        return self._tasks_dir / tid

    def prd_path(self, tid: str) -> Path:
        return self._tasks_dir / tid / "prd.md"

    def archived_path(self, tid: str) -> Optional[Path]:
        hits = list(self.archive_dir.glob(f"*/*/{tid}")) if self.archive_dir.exists() else []
        return hits[0] if hits else None
def _prd_data(snap: Snapshot, tid: str) -> list[dict[str, Any]]:
    prd = snap.prd_path(tid)
    return _prd_parse(prd.read_text(encoding="utf-8", errors="replace")) if prd.exists() else []
def _prd_parse(text: Optional[str]) -> list[dict[str, Any]]:
    # 解析 prd.md 目标/验收标准 两节: checklist (勾选态) + prose 直显; 跳 TODO 占位
    if not text:
        return []
    secs: dict[str, list[tuple[str, bool, str]]] = {}
    cur: Optional[str] = None
    for ln in text.splitlines():
        h = re.match(r"^#{1,6}\s+(.+?)\s*$", ln)
        if h:
            cur = h.group(1).strip() if h.group(1).strip() in ("目标", "验收标准") else None
            continue
        if not cur:
            continue
        m = re.match(r"^\s*[-*]\s+\[([ xX])\]\s+(.+?)\s*$", ln)
        if m:
            txt = m.group(2).strip()
            if not txt.lstrip().startswith("TODO"):
                secs.setdefault(cur, []).append(("check", m.group(1).lower() == "x", txt))
            continue
        txt = re.sub(r"^\s*[-*]\s+", "", ln).strip()
        if txt and not txt.lstrip().startswith("TODO"):
            secs.setdefault(cur, []).append(("prose", False, txt))
    out: list[dict[str, Any]] = []
    for name in ("目标", "验收标准"):
        items = secs.get(name)
        if not items:
            continue
        checks = [d for k, d, _ in items if k == "check"]
        badge: Optional[list[int]] = [sum(1 for c in checks if c), len(checks)] if checks else None
        prose_cls = ""  # 目标/验收标准 一致: 非 checkbox 行也渲 todo ○/● 标记 (不再对验收段打 .prose 去标记)
        out.append({
            "name": name, "badge": badge,
            "items": [{"kind": k, "done": bool(d), "text": tt,
                       "proseCls": ("" if k == "check" else prose_cls)}
                      for k, d, tt in items],
        })
    return out
def _view_board_data(snap: Snapshot) -> dict[str, Any]:
    # 结构化看板数据 (GET /__skein__/data); 呈现全由 webapp 前端做。
    # 业务逻辑 (pct/耗时/聚合/next-up/prd 解析) 留此当数据, 不拼 HTML; DAG 由前端从 cards 推。
    # git 仓库用户名 (作为默认负责人)
    git_user: Optional[str] = None
    try:
        r = git("config", "user.name", check=False, cwd=snap._tasks_dir)
        if r.returncode == 0 and r.stdout.strip():
            git_user = r.stdout.strip()
    except Exception:
        pass

    def fmt_dur(mins: Optional[int]) -> str:
        if mins is None:
            return "-"
        return f"{mins}m" if mins < 60 else f"{mins // 60}h{mins % 60:02d}m"

    tnow = now()
    tasks = sorted(snap.tasks, key=lambda t: (STATUS_ORDER.get(t["status"], 9), -(t.get("started") or 0)))
    name_of: dict[str, str] = {t["id"]: t.get("name", t["id"]) for t in tasks}

    def elapsed_of(t: dict[str, Any]) -> int:
        st = t.get("status")
        if st in (S_PENDING, S_RESEARCH):
            return 0
        start = t.get("started") or t.get("created")
        if not start:
            return 0
        end = t.get("finished") if (st == S_DONE and t.get("finished")) else tnow
        return cast(int, round((end - start) / 60))

    def task_pct(t: dict[str, Any]) -> int:
        # ponytail: 委托全局三阶段加权 _task_pct (保留闭包名兼容 board 内多处引用)
        return _task_pct(t)

    def node(_id: str, nm: str, stt: str, deps: Any, pct: int, desc: Any) -> list[Any]:
        # DAG 节点统一为数组 [id, name, status, deps(id 数组), pct, desc]
        return [_id, nm, stt, [d for d in (deps or [])], pct, desc or ""]

    # 概览聚合
    cnt: dict[str, int] = {}
    elapsed_total = 0
    for t in tasks:
        cnt[t["status"]] = cnt.get(t["status"], 0) + 1
        elapsed_total += elapsed_of(t)

    # task+subtask 综合进度: 按 subtask 粒度均摊 (combinedPct, dashboard 用); 无 subtask 的 task 整体算一个节点
    has_sub = any(t.get("subtasks") for t in tasks)
    leaves: dict[str, list[str]] = {}
    for t in tasks:
        subs = t.get("subtasks", [])
        if subs:
            depd = {d for s in subs for d in s.get("depends_on", [])}
            leaves[t["id"]] = [f'{t["id"]}/{s["sid"]}' for s in subs if s["sid"] not in depd] \
                or [f'{t["id"]}/{subs[-1]["sid"]}']
        else:
            leaves[t["id"]] = [t["id"]]
    combined: list[list[Any]] = []
    for t in tasks:
        subs = t.get("subtasks", [])
        prereq = [nid for d in t.get("deps", []) for nid in leaves.get(d, [d])]
        if not subs:
            combined.append(node(t["id"], t.get("name", t["id"]), t["status"], prereq,
                                 task_pct(t), t.get("desc", "")))
            continue
        intra = {s["sid"] for s in subs}
        for s in subs:
            sid = f'{t["id"]}/{s["sid"]}'
            sdeps = [f'{t["id"]}/{d}' for d in s.get("depends_on", []) if d in intra]
            if not sdeps:
                sdeps = list(prereq)
            combined.append(node(sid, s.get("name", s["sid"]), s["status"], sdeps,
                                 _sub_pct(s), s.get("desc", "")))
    combined_pct = round(sum(n[4] for n in combined) / len(combined)) if combined else 0

    est_meta = f'已耗 {fmt_dur(elapsed_total or None)}' if elapsed_total else ''

    # 两池占用 (design.md §3): work = 全局 running subtask (phase exec+research 共用一池);
    # gate = 检查中+收尾中 task 数。两池独立计数, 与 s4 调度器的槽位判定同一口径。
    work_running = sum(1 for t in tasks for s in t.get("subtasks", []) if s.get("status") == SS_RUNNING)
    gate_running = cnt.get(S_CHECK, 0) + cnt.get(S_FINISHING, 0)

    # 下一个可执行: 无进行中态 task 时, 首个依赖已清的待处理 task (可 skein confirm 开工)
    next_up_id: Optional[str] = None
    if not any(cnt.get(s, 0) for s in STATUS_ACTIVE):
        next_up_id = next((t["id"] for t in tasks
                           if t["status"] == S_PENDING
                           and not any(snap.dep_unfinished(d) for d in t.get("deps", []))), None)

    prd_data: Callable[[str], list[dict[str, Any]]] = lambda tid: _prd_data(snap, tid)  # noqa: E731 — 实现提到模块级 _prd_data (detail 端点复用)

    cards: list[dict[str, Any]] = []
    for t in tasks:
        subs = t.get("subtasks", [])
        sname_of = {s["sid"]: s.get("name", s["sid"]) for s in subs}
        sdone = sum(1 for s in subs if s["status"] == SS_DONE)
        snodes = [node(s["sid"], s.get("name", s["sid"]), s["status"], s.get("depends_on", []),
                       _sub_pct(s), s.get("desc", "")) for s in subs]
        subtable = [{
            "sid": s["sid"], "name": s["name"], "status": s["status"], "pct": _sub_pct(s),
            "estimate": s.get("estimate"),  # 预计工时(小时); 前端 ETA 逐项累加用
            "skills": s.get("skills", []),
            "dependsOn": s.get("depends_on", []),
            "depNames": [sname_of.get(d, d) for d in s.get("depends_on", [])],
            "acc": s.get("验收", []),
            "created": s.get("created"),
            "started": s.get("started"),
            "finished": s.get("finished"),
        } for s in subs]
        cards.append({
            "id": t["id"], "name": t.get("name") or t["id"], "status": t["status"], "desc": t.get("desc", ""),
            "stage": _task_stage(t),
            "parent": t.get("parent"), "kind": t.get("kind", "task"),  # task 级父子层 (supertask 分组用, 数据就绪; 前端分组渲染待补)
            "nextUp": t["id"] == next_up_id,
            "deps": t.get("deps", []),
            "depNames": [name_of.get(d, d) for d in t.get("deps", [])],
            "worktree": (t.get("worktree") or None) if snap.wt_shown else None,
            "assignee": t.get("assignee") or t.get("owner") or git_user,
            "created": t.get("created"),
            "confirmed": t.get("confirmed"),
            "started": t.get("started"),
            "checked": t.get("checked"),
            "finished": t.get("finished"),
            "elapsed": elapsed_of(t),
            "estimate": t.get("estimate"),  # task 预计工时(小时) = Σ subtask + plan/check 自身开销
            "priority": t.get("priority") or PRIORITY_DEFAULT,  # 看板卡片/详情面板优先级 (真实值; 未存则中档)
            "sdone": sdone, "stotal": len(subs), "spct": task_pct(t),
            "prd": prd_data(t["id"]),
            "subtable": subtable,
            "subNodes": snodes,
        })

    return {
        "proj": snap.proj,
        "overview": {
            "taskCount": len(tasks),
            "stats": {S_DONE: cnt.get(S_DONE, 0), S_ACTIVE: cnt.get(S_ACTIVE, 0),
                      S_CHECK: cnt.get(S_CHECK, 0), S_FINISHING: cnt.get(S_FINISHING, 0),
                      S_RESEARCH: cnt.get(S_RESEARCH, 0), S_PENDING: cnt.get(S_PENDING, 0)},
            "estMeta": est_meta,
            "maxActive": snap.pool_work,  # 兼容旧字段: 前端 ETA 折算并行墙钟用, 语义即 pools.work.limit
            "pools": {"work": {"limit": snap.pool_work, "running": work_running},
                      "gate": {"limit": snap.gate_active, "running": gate_running}},
            "combinedPct": combined_pct,
            "hasSub": has_sub,
        },
        "cards": cards,
    }
def _view_task_detail(snap: Snapshot, tid: str) -> Optional[dict[str, Any]]:
    # task.json 全文 + prd/design/findings 原文 + subtask + 契约; 未归档缺失则回落归档目录
    tdir = snap.task_path(tid)
    archived = False
    if not (tdir / "task.json").exists():
        ap = snap.archived_path(tid)
        if ap:
            tdir, archived = ap, True
    tj = tdir / "task.json"
    if not tj.exists():
        return None
    try:
        data = json.loads(tj.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    docs: dict[str, Any] = {}
    for fn in ("prd.md", "design.md", "findings.md"):
        f = tdir / fn
        docs[fn[:-3]] = f.read_text(encoding="utf-8", errors="replace") if f.exists() else None
    # research 目录多篇笔记: {filename: content} (无目录或空则空 dict)
    research: dict[str, str] = {}
    rdir = tdir / "research"
    if rdir.is_dir():
        for rf in sorted(rdir.glob("*.md")):
            research[rf.name] = rf.read_text(encoding="utf-8", errors="replace")
    # 依赖明细直接内联 — 详情页据此渲染前置/被依赖, 无需再拉 /data 全量看板
    deps = data.get("deps", [])
    dep_tasks: list[dict[str, Any]] = []
    dependents: list[dict[str, Any]] = []
    for t in snap.all_tasks:
        brief = {"id": t["id"], "name": t.get("name") or t["id"],
                 "status": t.get("status"), "desc": t.get("desc", "")}
        if t["id"] in deps:
            dep_tasks.append(brief)
        if tid in t.get("deps", []):
            dependents.append(brief)
    # 父子关系: supertask → child task 列表; child → parent task 信息
    parent_id = data.get("parent")
    parent_task = None
    child_tasks: list[dict[str, Any]] = []
    if parent_id:
        for t in snap.all_tasks:
            if t["id"] == parent_id:
                parent_task = {"id": t["id"], "name": t.get("name") or t["id"],
                               "status": t.get("status"), "desc": t.get("desc", "")}
                break
    if data.get("kind") == "supertask":
        for t in snap.all_tasks:
            if t.get("parent") == tid:
                child_tasks.append({"id": t["id"], "name": t.get("name") or t["id"],
                                    "status": t.get("status"), "desc": t.get("desc", ""),
                                    "progress": _task_pct(t)})
    return {"task": data, "docs": docs, "research": research, "archived": archived,
            "subtasks": data.get("subtasks", []), "contracts": data.get("contracts", []),
            "maxActive": snap.pool_work,  # 前端 ETA 折算并行墙钟用
            "prd": _prd_parse(docs.get("prd")), "progress": _task_pct(data),
            "stage": _task_stage(data), "depTasks": dep_tasks, "dependents": dependents,
            "parentTask": parent_task, "childTasks": child_tasks}
def _view_archive_list(snap: Snapshot) -> list[dict[str, Any]]:
    # 已归档 task 列表 (archive/<年>/<月-日>/<id>)
    out: list[dict[str, Any]] = []
    if snap.archive_dir.exists():
        for d in sorted(snap.archive_dir.glob("*/*/*")):
            tj = d / "task.json"
            if not tj.exists():
                continue
            try:
                t = json.loads(tj.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            out.append({"id": t.get("id", d.name), "name": t.get("name", d.name),
                        "status": t.get("status"), "desc": t.get("desc", ""),
                        "finished": t.get("finished"), "archivedAt": d.parent.name,
                        "subs": len(t.get("subtasks", []))})
    return out
def _view_archive(snap: Snapshot) -> dict[str, Any]:
    # 归档页数据源 (端点自足, 归档页不再拉 /data 全量看板):
    #   archive/ 目录内已归档 task + 仍在 task/ 内的已完成 task (尚未到保留期)
    tasks = list(_view_archive_list(snap))
    tasks += [{"id": t["id"], "name": t.get("name", t["id"]), "desc": t.get("desc", ""),
               "status": t["status"], "created": t.get("created"),
               "started": t.get("started"), "finished": t.get("finished"),
               "subs": len(t.get("subtasks", []))}
              for t in snap.tasks if t["status"] == S_DONE]
    return {"tasks": tasks}
def _view_dashboard(snap: Snapshot) -> dict[str, Any]:
    # 统计聚合: 复用 board_data overview + 补 subtask 状态分布 + 完成率
    data = _view_board_data(snap)
    ov = data["overview"]
    sub_stat: dict[str, int] = {}
    for c in data["cards"]:
        for s in c.get("subtable", []):
            sub_stat[s["status"]] = sub_stat.get(s["status"], 0) + 1
    total = ov["taskCount"]
    done = ov["stats"].get(S_DONE, 0)
    # 进行中 subtask: active task 内 SS_RUNNING (含耗时)
    tnow = now()
    running_subs: list[dict[str, Any]] = []
    for t in snap.active:
        for s in t.get("subtasks", []):
            if s.get("status") != SS_RUNNING:
                continue
            started = s.get("started")
            running_subs.append({
                "tid": t["id"], "sid": s["sid"], "name": s.get("name", s["sid"]),
                "elapsed": round((tnow - started) / 60) if started else None,
            })
    # 就绪 subtask: active task 内 pending 且依赖全 done (不受空闲槽限, 展示全量就绪)
    ready_subs: list[dict[str, Any]] = []
    for t in snap.active:
        done_sids = {s["sid"] for s in t.get("subtasks", []) if s.get("status") == SS_DONE}
        for s in t.get("subtasks", []):
            if s.get("status") != SS_PENDING:
                continue
            if not all(d in done_sids for d in s.get("depends_on", [])):
                continue
            ready_subs.append({
                "tid": t["id"], "sid": s["sid"], "name": s.get("name", s["sid"]),
                "depends_on": s.get("depends_on", [])})
    # 「就绪待启动」中间态已随 confirm 吸收 start 删除 (design.md §1) — 待处理 task 前置一清即可
    # confirm 直接开工, 不再有单独一批"排队等启动"的 task。readyTasks 保留字段 (前端兼容) 恒空。
    ready_tasks: list[dict[str, Any]] = []
    # 待 plan task: 所有 status=待处理 (含未 confirm; subCount=0 即 plan 未收敛)
    to_plan_tasks = [{"id": t["id"], "name": t.get("name", t["id"]),
                      "desc": t.get("desc", ""), "subCount": len(t.get("subtasks", []))}
                     for t in snap.all_tasks if t["status"] == S_PENDING]
    # 执行中 / 检查中 task: 一趟遍历分流 (cards 已含 elapsed/sdone/stotal/pct, 不重算)
    active_tasks: list[dict[str, Any]] = []
    check_tasks: list[dict[str, Any]] = []
    for c in data["cards"]:
        if c["status"] not in (S_ACTIVE, S_CHECK):
            continue
        row = {"id": c["id"], "name": c.get("name", c["id"]), "status": c["status"],
               "pct": c["spct"], "sdone": c["sdone"], "stotal": c["stotal"],
               "elapsed": c.get("elapsed")}
        (active_tasks if c["status"] == S_ACTIVE else check_tasks).append(row)
    # 首页最近列表: 端点自足 (首页不再拉 /data 全量看板), 按最近活动时间倒序
    def brief(t: dict[str, Any]) -> dict[str, Any]:
        return {"id": t["id"], "name": t.get("name", t["id"]), "desc": t.get("desc", ""),
                "status": t["status"], "created": t.get("created"),
                "started": t.get("started"), "finished": t.get("finished")}
    recent = sorted(snap.tasks,
                    key=lambda t: -(t.get("finished") or t.get("started") or t.get("created") or 0))
    recent_active = [brief(t) for t in recent
                     if t["status"] in (S_PENDING, S_RESEARCH, S_ACTIVE, S_CHECK, S_FINISHING)][:8]
    recent_done = [brief(t) for t in recent if t["status"] == S_DONE][:5]
    # 总览 ETA 的输入: 只挑 etaOf 真正要读的字段下发 (前端 normalizeTask 会把 subtable→subtasks、
    # spct→progress 适配好)。**不在 Python 侧算 ETA** —— 关键路径/并发折算/实测校准那套算法在
    # assets/nextjs/src/lib/eta.ts 已有一份, 再写一份必然漂移。
    eta_cards = [{
        "id": c["id"], "status": c["status"], "estimate": c["estimate"],
        "spct": c["spct"], "deps": c["deps"],
        "subtable": [{"sid": s["sid"], "status": s["status"], "pct": s["pct"],
                      "estimate": s["estimate"], "dependsOn": s["dependsOn"],
                      "started": s["started"], "finished": s["finished"]}
                     for s in c["subtable"]],
    } for c in data["cards"]]

    return {"proj": snap.proj, "taskCount": total,
            "maxActive": snap.pool_work,   # 前端折算并行墙钟用
            "etaCards": eta_cards,
            "recentActive": recent_active, "recentDone": recent_done,
            "doneRate": round(done / total * 100) if total else 0,
            "activeCount": ov["stats"].get(S_ACTIVE, 0) + ov["stats"].get(S_CHECK, 0),
            "combinedPct": ov["combinedPct"], "statusDist": ov["stats"],
            "subStatusDist": sub_stat, "estMeta": ov["estMeta"],
            "runningSubs": running_subs, "readySubs": ready_subs,
            "readyTasks": ready_tasks, "toPlanTasks": to_plan_tasks,
            "activeTasks": active_tasks, "checkTasks": check_tasks}
def _view_queue(snap: Snapshot) -> dict[str, Any]:
    # 待执行队列 (web 展示, 不受槽限): 全量 pending subtask 队列 + active 内全量就绪 subtask。
    # 「就绪待启动」task 中间态已随 confirm 吸收 start 删除 (design.md §1), readyTasks 恒空
    # (前端字段兼容; 待处理 task 前置一清即可直接 confirm 开工, 不再有单独排队态)。
    tasks = snap.tasks
    ready_tasks: list[dict[str, Any]] = []
    # web 展示不受槽限: pending 且依赖全 done 即列 (与 dashboard readySubs 同, 受槽限只作用于 claim/exec 派发)
    ready_subs: list[dict[str, Any]] = []
    for t in snap.active:
        done_sids = {s["sid"] for s in t.get("subtasks", []) if s.get("status") == SS_DONE}
        for s in t.get("subtasks", []):
            if s.get("status") != SS_PENDING:
                continue
            if not all(d in done_sids for d in s.get("depends_on", [])):
                continue
            ready_subs.append({"tid": t["id"], "sid": s["sid"],
                               "name": s.get("name", s["sid"]),
                               "desc": s.get("desc", ""), "status": s["status"],
                               "depends_on": s.get("depends_on", [])})
    # 执行中 task / running sub: 复用 tasks (已 _render_tasks) + active 内 SS_RUNNING
    tnow = now()
    running_subs: list[dict[str, Any]] = []
    for t in snap.active:
        for s in t.get("subtasks", []):
            if s.get("status") != SS_RUNNING:
                continue
            started = s.get("started")
            running_subs.append({"tid": t["id"], "sid": s["sid"], "name": s.get("name", s["sid"]),
                                 "elapsed": round((tnow - started) / 60) if started else None})
    # ponytail: active_tasks 自算, 复用 tasks 避免二次扫描 (字段对齐 board_data.cards)
    active_tasks: list[dict[str, Any]] = []
    for t in tasks:
        if t["status"] not in STATUS_INFLIGHT:
            continue
        subs = t.get("subtasks", [])
        st = t.get("status")
        start = t.get("started") or t.get("created")
        if st == S_DONE and t.get("finished"):
            end = t.get("finished")
        else:
            end = tnow
        elapsed = round((end - start) / 60) if start and st != S_PENDING else 0
        active_tasks.append({"id": t["id"], "name": t.get("name", t["id"]), "status": st,
                             "pct": _task_pct(t),
                             "sdone": sum(1 for s in subs if s["status"] == SS_DONE),
                             "stotal": len(subs), "elapsed": elapsed})
    # task 级队列: 未完成的全量 (端点自足, 队列页不再拉 /data 全量看板)
    queue_tasks = [{"id": t["id"], "name": t.get("name", t["id"]), "desc": t.get("desc", ""),
                    "status": t["status"], "priority": t.get("priority"),
                    "created": t.get("created"), "started": t.get("started"),
                    "spct": _task_pct(t)}
                   for t in tasks if t["status"] in (S_PENDING, S_RESEARCH, S_ACTIVE, S_CHECK, S_FINISHING)]
    return {"pendingQueue": _pending_queue(tasks, snap.dep_unfinished),
            "queueTasks": queue_tasks,
            "readyTasks": ready_tasks, "readySubtasks": ready_subs,
            "activeTasks": active_tasks, "runningSubs": running_subs}
def _view_search(snap: Snapshot, q: Any) -> dict[str, Any]:
    # 跨 task/subtask/prd/spec 关键词 (子串, 不分词): 命中即返回一条 {kind,id,name,snippet}
    q = (q or "").strip().lower()
    if not q:
        return {"query": q, "hits": []}
    hits: list[dict[str, Any]] = []
    for t in snap.tasks:
        if q in " ".join(str(x or "") for x in (t["id"], t.get("name", ""), t.get("desc", ""))).lower():
            hits.append({"kind": "task", "id": t["id"],
                         "name": t.get("name", t["id"]), "snippet": t.get("desc", "")})
        for s in t.get("subtasks", []):
            if q in " ".join(str(x or "") for x in (s["sid"], s.get("name", ""), s.get("desc", ""))).lower():
                hits.append({"kind": "subtask", "id": f'{t["id"]}/{s["sid"]}',
                             "name": s.get("name", s["sid"]), "snippet": s.get("desc", "")})
        prd = snap.prd_path(t["id"])
        if prd.exists() and q in prd.read_text(encoding="utf-8", errors="replace").lower():
            hits.append({"kind": "prd", "id": t["id"],
                         "name": f'{t.get("name", t["id"])} · PRD', "snippet": ""})
    root = snap.spec_root
    if root.exists():
        for f in sorted(root.rglob("*.md")):
            if f.name == "index.md":
                continue
            if q in f.read_text(encoding="utf-8", errors="replace").lower():
                rel = f.relative_to(root).as_posix()
                hits.append({"kind": "spec", "id": rel, "name": rel, "snippet": ""})
    return {"query": q, "hits": hits}
def _fmt_ts(ts: Optional[int]) -> str:
    # epoch 秒 → 本地可读时间; None/0 → "-"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) if ts else "-"
class DataSource(Protocol):
    """serve 层 (build_app) 消费的只读数据面 seam — Skein 结构性满足 (无需继承)。
    真实 Skein + 测试假源 = 两个 adapter, 令路由脱 uvicorn 经 TestClient 单测。

    **只暴露 `_snapshot()`, 不逐个视图开口子**: 六个视图本来就是 `_view_*(Snapshot)` 的纯函数,
    从前 Skein 上挂了 7 个 `return _view_x(self._snapshot())` 的转发方法, 接口宽度等于实现宽度
    (shallow)。收成一个方法后, 增删视图端点不再需要动这份 Protocol —— 视图是 build_app 自己调
    纯函数的事。列出的其余成员 = build_app 实际用到的全部, 增删端点依赖须同步此处。"""
    dir: Path
    root: Path
    tasks: Path
    _LOCK_ID_PATH: str
    _REV_PATH: str
    _LIVE_PATH: str
    def _asset_rev(self) -> str: ...
    def _data_rev(self) -> str: ...
    def _task_json_rev(self) -> str: ...
    def _snapshot(self) -> "Snapshot": ...
    def _webapp_html(self) -> str: ...
    def _spec_rev(self) -> str: ...
    def _spec_tree(self) -> dict[str, Any]: ...
    def _spec_resolve(self, rel: Any) -> Optional[Path]: ...
    def _spec_meta(self, page: int = ..., page_size: int = ..., namespace: str = ...,
                   category: str = ..., keyword: str = ...) -> dict[str, Any]: ...
    def _spec_search(self, q: str) -> list[dict[str, Any]]: ...
    def _exec_argv(self, body: dict[str, Any]) -> Optional[list[str]]: ...
    def config(self) -> dict[str, Any]: ...
def _spec_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    # spec md 头部 `---` 包裹的 YAML 子集 → (meta, body)。解析归后端 (前端只渲染)。
    # 值形态: `key: value` / `key: [a,b]` (数组, 引号剥离)。无 frontmatter → ({}, 原文)。
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    if not m:
        return {}, text
    meta: dict[str, Any] = {}
    for ln in m.group(1).splitlines():
        kv = re.match(r"^([\w-]+):\s*(.*)$", ln)
        if not kv:
            continue
        v: Any = kv.group(2).strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
        else:
            v = v.strip("\"'")
        meta[kv.group(1)] = v
    return meta, text[m.end():]
def _cards_signature(data: dict[str, Any]) -> dict[str, tuple[Any, ...]]:
    # 取 cards 关键字段做 signature (变即推 task-changed); 不深比 desc/subtable 等重字段 (省 CPU)。
    # ponytail: O(n) n=task 数; signature tuple 含 status/pct/sdone/stotal/started/finished/worktree, 软刷覆盖此集变化。
    out: dict[str, tuple[Any, ...]] = {}
    for c in data.get("cards", []):
        out[c["id"]] = (c.get("status"), c.get("spct"), c.get("sdone"), c.get("stotal"),
                        c.get("started"), c.get("finished"), c.get("worktree"),
                        c.get("nextUp"), c.get("stage"), c.get("priority"))
    return out
