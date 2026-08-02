"""task.json 的落盘层 — **唯一写入口**。

## interface
`load / save / all_tasks / sync` 四个动词是这层对外的全部。其余 (`render_tasks` 看板并集读、
`archived_path` / `active` / `used_ids` 查询、`archive_task` 归档搬目录) 是围绕同一份数据的读侧。

## 内部吸收了什么
`write_if_changed` 增量写、`autoclean` 惰性归档、`_unfinished_related` 关联链保护、损坏
task.json 的跳过兜底、派生 .md 的同步刷新 —— 调用方一个都不需要知道。**save 一次, 该刷的
都刷了**, 这正是「唯一写入口」的意思: 从前每个改状态的命令都得记得自己去刷看板。

## 两个注入依赖, 不反向 import
`cfg_fn` (读 config.yaml) 与 `wt_shown_fn` (worktree 列是否展示) 由 Skein 传进来。这样
store 不认识 commands 层, 依赖是单向的。渲染同理: board.py 是纯函数, store 调它, 它不调 store。

## ponytail: 一次 sync 会把每个 task.json 读 5 遍
`sync` 里 `all_tasks()` 独立调 4 次 + `render_tasks()` 再扫一遍 (实测 15 个 task = 67 次
read_text / 5ms)。15 个 task 时无所谓, 上到几百再收敛成一次扫描 —— `views.Snapshot` 已是
现成的「一次扫描多视图」形状, 到时让 sync 也走它。
"""
from __future__ import annotations

import datetime
import json
import shutil
from pathlib import Path
from typing import Any, Callable, Optional, cast

from skeinlib.hooks.runner import DBG
from skeinlib.board import render_board, render_task_board, render_vision
from skeinlib.errors import SkeinError
from skeinlib.task.model import PRIORITY_DEFAULT, PRIORITY_RANK, STATUS_ACTIVE, STATUS_ORDER, TaskStatus, TS_CHECKED_END, now


class TaskStore:
    def __init__(self, dir_: Path, tasks: Path, archive_dir: Path,
                 cfg_fn: Callable[[], dict[str, Any]],
                 wt_shown_fn: Callable[[], bool]) -> None:
        self.dir = dir_
        self.tasks = tasks
        self.archive_dir = archive_dir
        self._cfg = cfg_fn
        self._wt_shown_fn = wt_shown_fn

    def autoclean(self, days: Optional[int] = None) -> list[str]:
        # 惰性归档: 已完成且超保留期的 task 移入 archive (保留期内留看板)。days 省略用 config retain_days。
        # 负数 = 永不自动清理。0 = finish 即归档 (旧行为)。每次 _sync 触发, 无需守护进程。
        d = days if days is not None else self._cfg().get("retain_days", 7)
        if d is None or int(d) < 0:
            return []
        cutoff = now() - int(d) * 86400
        snapshot = self.all_tasks()
        blocked = self._unfinished_related(snapshot)  # 关联链上有未完成 → 整条链不归档
        archived = []
        for t in snapshot:
            if t["id"] in blocked:
                continue
            if t["status"] == TaskStatus.DONE and t.get("finished", t.get("done_at", 0)) <= cutoff:
                self.archive_task(t["id"])
                archived.append(t["id"])
        return archived

    @staticmethod
    def _unfinished_related(tasks: list[dict[str, Any]]) -> set[str]:
        # 关联 = deps 双向 + parent/child 双向。任一连通分量内有非已完成 task, 该分量整体禁归档
        # (归档走了会切断上下文链: 未完成的兄弟/后继再回头查前置产物时目录已迁走)。
        adj: dict[str, set[str]] = {t["id"]: set() for t in tasks}
        for t in tasks:
            for other in list(t.get("deps") or []) + ([t["parent"]] if t.get("parent") else []):
                if other in adj:
                    adj[t["id"]].add(other)
                    adj[other].add(t["id"])
        status = {t["id"]: t["status"] for t in tasks}
        blocked: set[str] = set()
        seen: set[str] = set()
        for tid in adj:
            if tid in seen:
                continue
            comp, stack = set(), [tid]
            while stack:  # 连通分量整取
                cur = stack.pop()
                if cur in comp:
                    continue
                comp.add(cur)
                stack.extend(adj[cur] - comp)
            seen |= comp
            if any(status[c] != TaskStatus.DONE for c in comp):
                blocked |= comp
        return blocked

    def sync(self) -> None:
        # 顶层 task.json 唯一写入口: tasks 是未归档 task 的去规范化状态镜像 (per-task task.json 仍单一真值源),
        # 每次变更重算, 免各处同步。无 task 级 focus — 无未完成前置的 task 皆可并行 (DAG 就绪即跑)。
        self.autoclean()  # 惰性归档超保留期的完成 task, 再重算索引
        tasks = [{"id": t["id"], "status": t["status"], "deps": t["deps"],
                  "priority": t.get("priority") or PRIORITY_DEFAULT,
                  "worktree": t.get("worktree"),
                  "parent": t.get("parent"), "kind": t.get("kind", "task"),
                  "created": t.get("created"),
                  "confirmed": t.get("confirmed"),
                  "started": t.get("started"),
                  "checked": t.get("checked"),
                  "checked_end": t.get(TS_CHECKED_END),
                  "finished": t.get("finished")} for t in self.all_tasks()]
        self.write_if_changed(self.dir / "task.json",
            json.dumps({"tasks": tasks}, ensure_ascii=False, indent=2))
        self._write_board()  # 变更即刷 task.md (看板 http 实时渲染, 不落盘)
        for st in [t for t in self.all_tasks() if t.get("kind") == "supertask"]:
            self._write_vision(st)  # 每个 supertask 刷聚合看板 vision.md (有变更才写)

    def load(self, tid: str) -> dict[str, Any]:
        f = self.tasks / tid / "task.json"
        if not f.exists():
            raise SkeinError(f"task 不存在: {tid}")
        return cast(dict[str, Any], json.loads(f.read_text()))

    def save(self, t: dict[str, Any]) -> None:
        t["updated"] = now()
        # 先算 diff 再写: 内容未变则跳过 (增量, 不全量覆盖 → 免无谓 IO/mtime 抖动)
        self.write_if_changed(self.tasks / t["id"] / "task.json",
                               json.dumps(t, ensure_ascii=False, indent=2))
        self._write_task_board(t)  # task.json 唯一写入口 → 同步渲染子任务看板, 免各调用点漏刷 (task.json 变更即同步 task.md)

    def all_tasks(self) -> list[dict[str, Any]]:
        if not self.tasks.exists():
            return []
        out: list[dict[str, Any]] = []
        for d in sorted(self.tasks.iterdir()):
            if d.name == "archive":
                continue
            f = d / "task.json"
            if f.exists():
                try:
                    t = json.loads(f.read_text())
                except (json.JSONDecodeError, OSError) as e:
                    # 单个 task.json 损坏 (半写/手改坏) 不该炸整个看板: 跳过并告警, 其余 task 照常渲染
                    DBG.log(f"跳过损坏 {f}: {e}", style="red")
                    continue
                out.append(t)
                DBG.log(f"读 {f}  → id={t.get('id')} status={t.get('status')} "
                        f"subtasks={len(t.get('subtasks', []))} deps={t.get('deps') or '-'} "
                        f"contracts={len(t.get('contracts', []))}", style="dim")
        # 状态优先排序 (进行中>检查中>待处理>已完成), 同状态内按优先级降序 (紧急>高>中>低), 同优先级按 id 序
        out.sort(key=lambda t: (STATUS_ORDER.get(t.get("status", ""), 9),
                                -PRIORITY_RANK.get(t.get("priority", ""), PRIORITY_RANK[PRIORITY_DEFAULT]),
                                t.get("id") or ""))
        return out

    def render_tasks(self) -> list[dict[str, Any]]:
        # 看板专用读取: 顶层 task.json 索引 + 各 task/<id>/task.json 明细 并集为数据源。
        # per-task 目录是真值源 (有 subtask/desc/name, 明细胜出); 顶层镜像补齐目录被删/迁移丢失、
        # 仅存于索引的 task (只 id/status/deps/worktree), 免看板静默空白。
        # 只服务看板只读渲染; 调度/mutation 仍走严格 _all() (幽灵骨架不可派发/归档)。
        # ponytail: 顶层索引本就无 name 字段, 看板对幽灵骨架直接用 id 显示 (task 一向以 id 标识, 非降级);
        #           要恢复 subtask/desc 等完整明细需从有 per-task 目录的分支 checkout。
        DBG.rule("看板数据源合并 (顶层索引 ∪ per-task 明细)")
        tasks = self.all_tasks()
        DBG.log(f"per-task 明细: {len(tasks)} 个 (真值源, 明细胜出)", style="cyan")
        have = {t["id"] for t in tasks}
        mirror = self.dir / "task.json"
        mirrored = 0
        if mirror.exists():
            try:
                rows = json.loads(mirror.read_text()).get("tasks", [])
            except (json.JSONDecodeError, OSError):
                rows = []
            DBG.log(f"读顶层镜像 {mirror}  → {len(rows)} 条索引", style="dim")
            for r in rows:
                if r["id"] in have:  # per-task 明细已覆盖 → 保留明细, 跳过镜像骨架
                    continue
                tasks.append({"id": r["id"], "name": r.get("name", r["id"]), "status": r["status"],
                              "priority": r.get("priority") or PRIORITY_DEFAULT,
                              "deps": r.get("deps", []), "worktree": r.get("worktree"),
                              "parent": r.get("parent"), "kind": r.get("kind", "task")})
                mirrored += 1
                DBG.log(f"  + 镜像补齐幽灵骨架 {r['id']} (per-task 目录缺失, 仅顶层索引可用)", style="yellow")
        else:
            DBG.log(f"顶层镜像 {mirror} 不存在, 仅用 per-task 明细", style="dim")
        tasks.sort(key=lambda t: (STATUS_ORDER.get(t["status"], 9),
                                  -PRIORITY_RANK.get(t.get("priority", ""), PRIORITY_RANK[PRIORITY_DEFAULT]),
                                  t["id"]))
        by_status: dict[str, int] = {}
        sub_total = 0
        sub_by_status: dict[str, int] = {}
        with_sub = 0
        for t in tasks:
            by_status[t["status"]] = by_status.get(t["status"], 0) + 1
            subs = t.get("subtasks", [])
            if subs:
                with_sub += 1
            sub_total += len(subs)
            for s in subs:
                ss = s.get("status", "?")
                sub_by_status[ss] = sub_by_status.get(ss, 0) + 1
        DBG.log(f"subtask 统计: 合计 {sub_total} 个, 分布于 {with_sub} 个 task "
                f"(其余 {len(tasks) - with_sub} 个无 subtask/幽灵骨架)", style="cyan")
        DBG.kv({"合计 task": len(tasks), "明细": len(tasks) - mirrored, "镜像补齐": mirrored,
                **{f"状态·{k}": v for k, v in by_status.items()},
                "合计 subtask": sub_total, "含 subtask 的 task": with_sub,
                **{f"subtask·{k}": v for k, v in sub_by_status.items()}}, title="看板数据源汇总")
        return tasks

    def archived_path(self, tid: str) -> Optional[Path]:
        # 归档嵌套: archive/<年>/<月-日>/<id>
        hits = list(self.archive_dir.glob(f"*/*/{tid}")) if self.archive_dir.exists() else []
        return hits[0] if hits else None

    def active(self) -> list[dict[str, Any]]:
        return [t for t in self.all_tasks() if t["status"] in STATUS_ACTIVE]

    def used_ids(self) -> set[str]:
        used = {p.name for p in self.tasks.iterdir() if p.name != "archive"} if self.tasks.exists() else set()
        used |= {p.name for p in self.archive_dir.glob("*/*/*")} if self.archive_dir.exists() else set()
        return used

    def archive_task(self, tid: str) -> None:
        src = self.tasks / tid
        if not src.exists():
            return
        d = datetime.datetime.now()
        dst = self.archive_dir / d.strftime("%Y") / d.strftime("%m-%d") / tid
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.move(str(src), str(dst))

    @staticmethod
    def write_if_changed(path: Path, content: str) -> None:
        # 渲染派生文件 (task.md) 每次变更重算, 但内容常与盘上相同 —
        # 先比对再写, 免无谓 IO/SSD 写入 (增量保护磁盘)。
        try:
            if path.exists() and path.read_text() == content:
                DBG.log(f"= {path}  (内容未变, 跳过写)", style="dim")
                return
        except OSError:
            pass
        path.write_text(content)
        DBG.log(f"✎ 写入 {path}  ({len(content)} 字符)", style="green")

    # ---- 派生 .md 渲染 (纯函数在 board.py, 本层只负责取数与写盘) ----
    def _write_board(self) -> None:
        self.write_if_changed(self.dir / "task.md",
                              render_board(self.render_tasks(), self._wt_shown_fn()))

    def _write_task_board(self, t: dict[str, Any]) -> None:
        pools = self._cfg()["pools"]
        self.write_if_changed(self.tasks / t["id"] / "task.md",
                              render_task_board(t, pools["work"], pools["gate"]))

    def _write_vision(self, st: dict[str, Any]) -> None:
        children = [c for c in self.render_tasks() if c.get("parent") == st["id"]]
        self.write_if_changed(self.tasks / st["id"] / "vision.md", render_vision(st, children))
