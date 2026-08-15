"""`Lifecycle` — task 状态机: 待处理 ⇄ 调研中 → 进行中 → 检查中 ⇄ 待处理 (revert 回退) → 收尾中 → 已完成, 外加删/改名。

## 这个类的边界
只管**一个 task 自身的状态迁移与计划字段** (deps/estimate/repos)。不碰调度 (归 `Scheduler`)、
不碰只读投影 (归 `Query`)、不碰 design 工件 (归 `Artifacts`)、不碰工作区级命令 (归 `Admin`)。

## 依赖为什么是构造入参
`ws` 给路径/配置/落盘/钩子, `doctor` 给 confirm 前置体检 (confirm 吸收原 start 的启动职责) —— 后者本来是 `DoctorMixin` 挂在门面
上的方法, 这里只要"能跑一次体检"这个能力, 不需要认识整个门面。注入一个可调用对象, 依赖就到此
为止, 不会顺着 `self` 摸到别的东西。
"""
from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from skeinlib.core.workspace import Workspace

from skeinlib.task.dag import _sub_estimate_sum, detect_cycle
from skeinlib.utils.errors import SkeinError
from skeinlib.task.model import (CODE_ID_RE, PRIORITY_DEFAULT, SLUG_RE, SubtaskStatus, STATUS_INFLIGHT,
                                 TaskStatus, ESTIMATE_HINT, parse_hours, now)
from skeinlib.task.design import validate_seam
from skeinlib.task.specfile import load_spec, save_spec, scaffold_spec, validate_spec as _spec_ready
from skeinlib.task import timeline as _timeline
from skeinlib.task.priority import validate_priority
from skeinlib.infra.worktree import commit_all, destroy_worktrees, git, make_worktree, parse_repos, worktrees_of

import json
import shutil
import sys
from typing import Callable, Optional


# 强制路径的 timeline 留痕: 看板上的强制按钮跳的是前置门, 动作照跑 —— 事后要能看出这一步是强制的。
_FORCE_NOTE = "--force: 看板强制操作, 跳过前置门"


def _review_summary(tid: str, t: dict[str, Any]) -> str:
	"""给用户人眼审核用的摘要 — 吃 task dict 返字符串。

	只摘**够判断该不该放行**的东西: TaskSpec 四要素 (desc/边界/验收/工时) + subtask 拆解。
	刻意不摘全文: 详细内容用户可以自己开 task.json 看, 终端里滚三屏反而没人读。
	"""
	subs = t.get("subtasks") or []
	sub_est = sum(float(s.get("estimate") or 0) for s in subs)
	b = t.get("boundary") or {}
	out = [f"── {tid}  {t.get('name') or tid} ──", f"   {t.get('desc') or ''}", ""]
	out.append(f"## 边界 (该做 {len(b.get('should') or [])} / 不该做 {len(b.get('should_not') or [])} 条)")
	out += [f"   + {ln}" for ln in (b.get("should") or [])] or ["   (空)"]
	out += [f"   × {ln}" for ln in (b.get("should_not") or [])]
	out.append("")
	acc = t.get("acceptance") or []
	out.append(f"## 验收标准 ({len(acc)} 条)")
	out += [f"   {i}. {ln}" for i, ln in enumerate(acc, 1)] or ["   (空)"]
	out.append("")
	out.append(f"## subtask ({len(subs)} 个, Σ工时 {sub_est:g}h)")
	for s in subs:
		dep = f" ← {','.join(s.get('depends_on') or [])}" if s.get("depends_on") else ""
		out.append(f"   [{s['sid']}] {s.get('name', '')} ({s.get('estimate') or '?'}h){dep}")
	out.append("")
	out.append(f"## 预计工时  task {t.get('estimate')}h  (Σsubtask {sub_est:g}h)")
	return "\n".join(out)


class Lifecycle:
    """task 状态机 + 计划字段编辑。"""

    def __init__(self, ws: "Workspace", doctor: Callable[[argparse.Namespace], Any]) -> None:
        self.ws = ws
        self._doctor = doctor

    # 下面这些是从 Skein 搬过来的方法体, 原样保留 —— 只把 self.X 改成 self.ws.X (见文件末尾说明)。
    def create(self, a: argparse.Namespace) -> dict[str, Any]:
        tid = a.id.strip()
        # 可读 id: 人工传入, 必须是 slug (kebab-case, 兼作 git 分支名 + 目录名)
        if not SLUG_RE.match(tid):
            raise SkeinError(
                f"非法 id: {tid!r} — 须为 kebab-case slug "
                "(小写字母/数字/连字符, 字母数字开头, 如 order-create-api)")
        if CODE_ID_RE.match(tid):
            raise SkeinError(
                f"id 须可读: {tid!r} 是字母+数字编号 — 用描述性 slug "
                "(如 order-create-api / user-auth), 勿用 t01 这类代号")
        if tid in self.ws.store.used_ids():
            raise SkeinError(f"id 已占用: {tid} — 换一个 (含已归档的也不可复用)")
        repos = parse_repos(getattr(a, "repos", None))
        if repos and not self.ws.config()["worktree"]["enabled"]:
            raise SkeinError(f"{tid} 声明 --repos 但 config worktree.enabled=false — 多子 git 隔离需启用 worktree")
        self.ws._stage_hooks("create", "before", self.ws._hook_ctx(tid))
        (self.ws.tasks / tid).mkdir(parents=True)
        deps = [d.strip() for d in (a.deps or "").split(",") if d.strip()]
        raw_est = getattr(a, "estimate", None)
        try:
            est = parse_hours(raw_est) if raw_est not in (None, "") else None
        except ValueError:
            raise SkeinError(f"预计工时非法: {raw_est!r} — {ESTIMATE_HINT}")
        self._scaffold(tid, a.name, a.desc, est)  # 落 prd.md (TaskSpec 载体) / design 脚手架
        t = {
            "id": tid, "name": a.name,
            "status": TaskStatus.PENDING, "deps": deps, "subtasks": [],
            "priority": validate_priority(getattr(a, "priority", None)),  # 四档枚举, 未指定落中档
            "repos": repos,          # planning 声明的目标子 git (rel 路径; 空=单根/原地模式)
            "worktree": None, "worktrees": [], "branch": f"skein/{tid}",
            "created": now(),        # 创建时刻
            "started": None,         # exec 时刻 (start 时置)
            "confirmed": None,       # confirm (吸收 start) 时刻
            "checked": None,         # 进入检查阶段时刻 (check 命令置)
            "checked_end": None,     # 检查结束时刻 (finishing 时置)
            "finished": None,        # 完成时刻 (finish 时置; 保留期从此计)
            "updated": now(),
        }
        cloned = self._clone_planning(tid, t, getattr(a, "like", None))
        _timeline.append(t, "task", TaskStatus.PENDING)
        self.ws.store.save(t)  # save 已渲染子任务看板 + 刷顶层索引
        self.ws._stage_hooks("create", "after", self.ws._hook_ctx(tid, t=t))
        out = {"id": tid, "path": str(self.ws.tasks / tid)}
        if cloned:
            out["cloned_from"] = cloned
        return out

    def _clone_planning(self, tid: str, t: dict[str, Any], src_id: str | None) -> str | None:
        """`--like <src>`: 把 src 的 TaskSpec/design/subtask 骨架搬过来, 状态全部重置。

        周期任务 (cron 巡检之类) 每轮都是同一份 planning, 从零重写 spec + design + subtask
        纯属重复劳动 —— 实测一个 cron 会话为同一个 intent 建了 5 个内容雷同的 task。
        已完成的 src 也能当模板 (done task 恰恰是最靠谱的模板)。
        """
        if not src_id:
            return None
        src = self.ws.store.load(src_id)  # 不存在直接 raise
        for fn in ("prd.md", "design.md"):  # prd.md 连 TaskSpec 一起克隆 (frontmatter 骨架)
            p = self.ws.tasks / src_id / fn
            if p.exists():
                (self.ws.tasks / tid / fn).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
        clones: list[dict[str, Any]] = []
        for s in src.get("subtasks") or []:
            c = {**s, "status": SubtaskStatus.PENDING, "acceptance_done": [],
                 "created": now(), "started": None, "finished": None}
            for k in ("note", "passed", "timeline"):  # 上一轮的执行期留痕, 不跟着克隆
                c.pop(k, None)
            clones.append(c)
        t["subtasks"] = clones
        return src_id  # estimate 随 prd.md 一起克隆 (TaskSpec 真值在 frontmatter)

    def _scaffold(self, tid: str, name: str, desc: str, est: float | None) -> None:
        """落 prd.md (TaskSpec frontmatter 载体) + design.md 脚手架。
        findings.md 不预建 — 仅真调研时由 skein-researcher 边研边增量生成 (无调研不产出)。
        模板极简 (只给骨架, 正文 planning 填), 避免占 token; 已存在则不覆盖。
        调度 DAG / 子任务不在此 — 归 task.json (脚本维护)。"""
        d = self.ws.tasks / tid
        files = {
            "prd.md": scaffold_spec(name, desc, est),
            "design.md": (
                f"# {name} — 详细设计\n\n"
                "架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):\n\n"
                "## 测试接缝 (seam)\n"
                "check 阶段验证的是`行为对不对`而非`跑没跑起来`, 全靠这里选对接缝。三条规则:\n"
                "1. 优先复用现有接缝, 不新建\n"
                "2. 取最高接缝 (越靠外部行为越好)\n"
                "3. 越少越好, 理想 = 1 个\n\n"
                "- [ ] TODO: 填测试接缝\n"),
        }
        for fn, body in files.items():
            p = d / fn
            if not p.exists():
                p.write_text(body)

    def repos(self, a: argparse.Namespace) -> dict[str, Any]:
        t = self.ws.store.load(a.id)
        if a.set is None:
            return {"id": a.id, "repos": t.get("repos") or []}
        if not self.ws.config()["worktree"]["enabled"]:
            raise SkeinError(f"{a.id} config worktree.enabled=false — worktree 禁用, 不可声明 repos")
        if t["status"] not in (TaskStatus.PENDING, TaskStatus.RESEARCH):
            raise SkeinError(f"{a.id} 状态 {t['status']}, repos 只能在 confirm 前 (待处理/调研中) 声明")
        t["repos"] = parse_repos(a.set)
        self.ws.store.save(t)
        return {"id": a.id, "repos": t["repos"]}

    def estimate(self, a: argparse.Namespace) -> dict[str, Any]:
        t = self.ws.store.load(a.id)
        if a.set is None:
            est = t.get("estimate")
            subsum = _sub_estimate_sum(t)
            return {"id": a.id, "estimate": est, "subtask_sum": subsum,
                    "overhead": round((est or 0) - subsum, 2) if subsum else None}
        if t["status"] not in (TaskStatus.PENDING, TaskStatus.RESEARCH):
            raise SkeinError(f"{a.id} 状态 {t['status']}, estimate 只能在 confirm 前 (待处理/调研中) 设置")
        try:
            val = parse_hours(a.set)
        except ValueError:
            raise SkeinError(f"预计工时非法: {a.set!r} — {ESTIMATE_HINT}")
        if val <= 0:
            raise SkeinError(f"预计工时须为正数: {val}")
        spec = load_spec(self.ws.tasks, a.id)
        spec["estimate"] = val
        save_spec(self.ws.tasks, a.id, spec)
        return {"id": a.id, "estimate": val}

    def spec(self, a: argparse.Namespace) -> dict[str, Any]:
        """TaskSpec 四要素的读/写 — 落盘 prd.md frontmatter (estimate 有专命令)。
        列表参数 (; 分号分隔多值); 不带任何参数 = 只读回显。"""
        t = self.ws.store.load(a.id)
        if all(getattr(a, k) is None for k in ("desc", "should", "not_", "acceptance")):
            return {"id": a.id, "desc": t.get("desc"),
                    "boundary": t.get("boundary") or {}, "acceptance": t.get("acceptance") or []}
        if t["status"] not in (TaskStatus.PENDING, TaskStatus.RESEARCH):
            raise SkeinError(f"{a.id} 状态 {t['status']}, spec 只能在 confirm 前 (待处理/调研中) 设置")
        spec = load_spec(self.ws.tasks, a.id)
        if a.desc is not None:
            spec["desc"] = a.desc
        b = dict(spec.get("boundary") or {})
        if a.should is not None:
            b["should"] = [x.strip() for x in a.should.split(";") if x.strip()]
        if a.not_ is not None:
            b["should_not"] = [x.strip() for x in a.not_.split(";") if x.strip()]
        spec["boundary"] = b
        if a.acceptance is not None:
            spec["acceptance"] = [x.strip() for x in a.acceptance.split(";") if x.strip()]
        save_spec(self.ws.tasks, a.id, spec)
        return {"id": a.id, "desc": spec.get("desc"), "boundary": spec["boundary"],
                "acceptance": spec.get("acceptance") or []}

    def priority(self, a: argparse.Namespace) -> dict[str, Any]:
        t = self.ws.store.load(a.id)
        if a.set is None:
            return {"id": a.id, "priority": t.get("priority") or PRIORITY_DEFAULT}
        t["priority"] = validate_priority(a.set)
        self.ws.store.save(t)
        return {"id": a.id, "priority": t["priority"]}

    def deps(self, a: argparse.Namespace) -> dict[str, Any]:
        t = self.ws.store.load(a.id)
        if a.set is None:
            return {"id": a.id, "deps": t.get("deps") or []}
        if t["status"] not in (TaskStatus.PENDING, TaskStatus.RESEARCH):
            raise SkeinError(f"{a.id} 状态 {t['status']}, deps 只能在 confirm 前 (待处理/调研中) 设置")
        if t.get("deps"):
            raise SkeinError(
                f"{a.id} 已有前置 {','.join(t['deps'])} — 既有依赖不可改 (deps 只补无前置的 task)")
        new = [d.strip() for d in (a.set or "").split(",") if d.strip()]
        ids = self.ws.store.used_ids()  # 含已归档, dep 指向归档 task 合法 (与 doctor 一致)
        for d in new:
            if d == a.id:
                raise SkeinError(f"{a.id} deps 自引用")
            if d not in ids:
                raise SkeinError(f"前置 task 不存在: {d}")
        # 环校验: 以拟设 deps 建全量未归档 task 级图, 检测环 (归档 task 不入图, 不成环)
        nodes = {x["id"] for x in self.ws.store.all_tasks()}
        graph = {x["id"]: [d for d in x.get("deps", []) if d in nodes] for x in self.ws.store.all_tasks()}
        graph[a.id] = [d for d in new if d in nodes]
        cycle_path = detect_cycle(graph)
        if cycle_path:
            raise SkeinError(f"deps 成环: {' -> '.join(cycle_path)}")
        t["deps"] = new
        self.ws.store.save(t)
        return {"id": a.id, "deps": new}

    def _validate_estimate(self, tid: str, t: dict[str, Any]) -> None:
        # confirm 硬门: 预计工时(小时)必须已填且为正数, 缺失/默认空 → 拒绝开工。
        # 且须自下而上累加: task 工时 ≥ Σ subtask 工时 (差额 = plan/check 等 task 自身开销),
        # 低于合计说明整体拍脑袋而非按实际要做的事逐项估。规则详见
        # skills/skein-plan/references/plan.md#预计工时硬门-estimate。
        est = t.get("estimate")
        if est is None or est == "" or not (isinstance(est, (int, float)) and est > 0):
            raise SkeinError(
                f"{tid} 预计工时未填 — 先 `skein task estimate {tid} --set <小时数>` 填实再 confirm")
        subsum = _sub_estimate_sum(t)
        if subsum and est < subsum:
            raise SkeinError(
                f"{tid} 预计工时 {est} h 低于 subtask 合计 {subsum} h — "
                f"task 工时须 ≥ Σ subtask + plan/check 自身开销, "
                f"`skein task estimate {tid} --set <≥{subsum}>`")

    def _planning_gaps(self, tid: str, t: dict[str, Any]) -> list[str]:
        """跑齐全部 planning 硬门, 返回未就绪项文案 (空 = 全过)。"""
        gaps: list[str] = []
        if not (t.get("subtasks") or []):
            gaps.append(f"无 subtask 登记 — `skein subtask add {tid} <sid> --name <标题> "
                        f"--desc <描述> --estimate <小时>`")
        gates: tuple[Callable[[], Any], ...] = (
            lambda: _spec_ready(self.ws.tasks, tid),
            lambda: validate_seam(self.ws.tasks, tid),
            lambda: self._validate_estimate(tid, t))
        for gate in gates:
            try:
                gate()
            except SkeinError as e:
                gaps.append(str(e).removeprefix(f"{tid} "))
        return gaps

    def research(self, a: argparse.Namespace) -> dict[str, Any]:
        # 待处理 → 调研中: 至少登记一个 phase=research 的 subtask (无调研诉求就不该进这态)。
        t = self.ws.store.load(a.id)
        if t["status"] != TaskStatus.PENDING:
            raise SkeinError(f"{a.id} 状态为 {t['status']}, 只能对待处理 (规划中) task 发起调研")
        if not (t.get("research_tasks") or []):
            raise SkeinError(
                f"{a.id} 无 research 任务 — 先 "
                f"`skein research add {a.id} <sid> --name <标题> --desc <描述> --estimate <小时>` 登记再发起调研")
        self.ws._stage_hooks("research", "before", self.ws._hook_ctx(a.id, t=t))
        t["status"] = TaskStatus.RESEARCH
        _timeline.append(t, "task", TaskStatus.RESEARCH)
        self.ws.store.save(t)
        self.ws._stage_hooks("research", "after", self.ws._hook_ctx(a.id, t=t))
        return {"id": a.id, "status": TaskStatus.RESEARCH}

    def plan(self, a: argparse.Namespace) -> dict[str, Any]:
        # 调研中 → 待处理: research subtask 须全 done, 调研的产出才算收敛成可规划的信息。
        # 调研中禁止直达开工态 —— confirm 会在 status=调研中 时直接拒绝, 提示先 plan。
        t = self.ws.store.load(a.id)
        if t["status"] != TaskStatus.RESEARCH:
            raise SkeinError(f"{a.id} 状态为 {t['status']}, 只能对调研中 task 收敛回规划")
        undone = [s["sid"] for s in t.get("research_tasks") or []
                 if s["status"] != SubtaskStatus.DONE]
        if undone:
            raise SkeinError(f"{a.id} research 任务未全完成: {', '.join(undone)} — 先 `skein research done` 它们再 plan")
        self.ws._stage_hooks("plan", "before", self.ws._hook_ctx(a.id, t=t))
        t["status"] = TaskStatus.PENDING
        _timeline.append(t, "task", TaskStatus.PENDING)
        self.ws.store.save(t)
        self.ws._stage_hooks("plan", "after", self.ws._hook_ctx(a.id, t=t))
        return {"id": a.id, "status": TaskStatus.PENDING}

    def confirm(self, a: argparse.Namespace) -> dict[str, Any]:
        """用户确认门 (待处理→进行中), **吸收原 `start` 的全部职责**: planning 完成 (TaskSpec 四要素
        填齐 + ≥1 subtask) 且用户评审通过后, doctor 体检 + 建 worktree,
        一步直接把 task 推进「进行中」——「就绪」中间态已删 (人审通过的下一秒就该开工, 没人真
        停在那儿, 见 design.md §1)。

        **不校验前置 task 是否完成**: confirm 只确认「这批审批做完了」, 是否可执行由调度侧
        取 subtask 时判 (`_schedulable` / `_ready` / `subtask start`)。把依赖门放这里会让一整
        批下游 task 在前置跑完前连审批都进行不了, 人审被迫串行化。
        """
        t = self.ws.store.load(a.id)
        force = bool(getattr(a, "force", False))
        # --force = 用户在看板上点了「确认规划」, 意图已明确, 只跳门不跳动作。
        # 仍限 confirm 前两态: 已开工的 task 再 _activate 会重复建 worktree/分支。
        if t["status"] == TaskStatus.RESEARCH and not force:
            raise SkeinError(f"{a.id} 调研中 — 先 `skein task plan {a.id}` 把调研收敛回规划再 confirm")
        if t["status"] != TaskStatus.PENDING and not (force and t["status"] == TaskStatus.RESEARCH):
            # 看板点了强制确认但 task 早已开工: 目标状态已达成, 幂等返回而非报错 —— 用户看到的
            # 是「点了没反应还弹错」, 而重跑 _activate 会重复建 worktree/分支, 两头都不能要。
            if force and t["status"] in STATUS_INFLIGHT:
                return {"id": a.id, "status": t["status"], "confirmed": True,
                        "worktrees": t.get("worktrees", []), "worktree": t.get("worktree"),
                        "note": "已是在途状态, 强制确认无需重复执行"}
            raise SkeinError(f"{a.id} 状态为 {t['status']}, 只能 confirm 待处理 (规划中) task")
        # planning 完成门: 无 subtask / TaskSpec 未填齐 / design 接缝占位 / 预计工时未填 → 拒绝开工。
        # 收集式而非 fail-fast: 四道门逐条报会逼调用方来回三四趟 (填 design → 撞 estimate),
        # 每趟都是一次完整往返。一次列全, 一次补齐。
        gaps = self._planning_gaps(a.id, t)
        if gaps and not force:
            raise SkeinError(
                f"{a.id} planning 未就绪 ({len(gaps)} 项待补):\n"
                + "\n".join(f"  {i}. {g}" for i, g in enumerate(gaps, 1)))
        if getattr(a, "summary", False):
            return {"summary": _review_summary(a.id, t)}
        channel = self._require_user_review(a.id, bool(getattr(a, "approved", False)),
                                            bool(getattr(a, "unattended", False)))
        # 吸收原 start 的前置校验: doctor 体检 + spec double-check (confirm 后被改空的兜底)
        self._doctor(a)
        self.ws._stage_hooks("confirm", "before", self.ws._hook_ctx(a.id, t=t))
        if not force:
            _spec_ready(self.ws.tasks, a.id)
        result = self._activate(t, channel, note=_FORCE_NOTE if force else "")
        return result

    def _activate(self, t: dict[str, Any], channel: str, note: str = "") -> dict[str, Any]:
        """待处理 → 进行中 的落盘动作: 置态 + 建 worktree + 落时间线。前置校验归调用方。"""
        a_id = t["id"]
        t["status"] = TaskStatus.ACTIVE
        t["confirmed"] = now()
        t["confirmed_by"] = channel  # 审核渠道留痕: ask (AskUserQuestion) / user-tty (终端交互)
        cfg = self.ws.config()
        repos = t.get("repos") or []
        wt_cfg = cfg["worktree"]["enabled"]
        wt_on = self.ws.git and wt_cfg  # 单根 worktree: 需根仓是 git; 配置禁用→原地执行
        # --repos 的 git 性由 _mkwt 逐子仓校验 (worktree 落各子仓内), 与父目录是否 git 无关 —
        # 故只在 config 显式禁用时挡, 不吃 self.ws.git (支持非 git 父 + 多 git 子的微服务布局)。
        if repos and not wt_cfg:
            raise SkeinError(
                f"{a_id} 声明了 --repos 但 config worktree.enabled=false — 多子 git 隔离需启用 worktree")
        if repos:
            # 多子 git: planning 声明的每个子 git 各开 worktree+branch (并列 repo / submodule 同理)
            t["worktrees"] = [make_worktree(t, r, cfg, self.ws.root) for r in repos]
            t["worktree"] = ", ".join(w["wt"] for w in t["worktrees"])  # 显示汇总
        elif wt_on:
            rel = f"{cfg['worktree']['root']}/skein-{a_id}"  # 相对 project root 存盘, 免机器绝对路径入库
            git("worktree", "add", "-b", t["branch"], str(self.ws.root / rel), "HEAD", cwd=self.ws.root)
            t["worktree"] = rel
            t["worktrees"] = [{"repo": ".", "wt": rel, "branch": t["branch"], "merged": False}]
        else:
            t["worktree"] = None  # 非 git / config 禁用, 无 repos: 原地执行, 无 worktree 隔离
            t["worktrees"] = []
        if not t.get("started"):
            t["started"] = now()  # exec 时刻 (首次 confirm; 重复不覆盖)
        _timeline.append(t, "task", TaskStatus.ACTIVE, note=note)
        self.ws.store.save(t)
        self.ws._stage_hooks("confirm", "after", self.ws._hook_ctx(a_id, t=t))
        return {"id": a_id, "status": TaskStatus.ACTIVE, "confirmed": True,
                "worktrees": t["worktrees"], "worktree": t["worktree"]}

    # ---- 人审门 (待处理→进行中 的最后一道) ----
    def _require_user_review(self, tid: str, approved: bool, unattended: bool = False) -> str:
        """规划必须经用户过目才允许开工。返回审核渠道 (写进 `confirmed_by`)。

        ## 为什么要有这道门
        前面三道 (TaskSpec 填齐 / ≥1 subtask / 预计工时) 校验的都是**结构**, AI 自己就能填满然后
        自己跑 confirm —— 于是「用户确认门」名存实亡, 一份没人看过的规划直接开了工。

        ## 🛑 本方法禁读 stdin
        CLI 的定位是被 skill / agent 调用的, **任何交互都会把调用方挂住** (等一个永远不来的
        输入)。曾经这里有一段 TTY 交互 (打印摘要 + 等用户敲 task id), 已整段删除。审核结果只
        以 `--approved` 这一个布尔量进来, 怎么拿到批准是调用方的事。

        ## 两条合法来源 (都是真实用户动作)
        | 来源 | 怎么走 |
        |---|---|
        | 看板点击 | 用户在 task 详情面板/详情页点「确认规划」→ `POST /__skein__/exec` 白名单转 `confirm <id> --approved`。**AI 没有浏览器, 点不了** |
        | 对话确认 | main 先 `confirm <id> --summary` 取摘要 → `AskUserQuestion` 请用户批准 → 带 `--approved` 再跑 |
        | 无人值守 | cron/CI 没有用户可问 → `--unattended` (需 `confirm.unattended=true` 预先授权), 留痕 `confirmed_by=unattended` |

        前者 AI 物理上做不到, 后者靠流程纪律 (`AskUserQuestion` 的答案 AI 伪造不了, 但"有没有
        真的问"这一步得 main 自觉) —— 与「有没有真的派 agent」同级。
        """
        if approved:
            return "user"
        if unattended:
            # 无人值守 (cron/CI): 没有用户可问, 传 --approved 只会是伪造。给一条留痕的合法路,
            # 但要用户在 config 里先授权一次 —— 否则这个 flag 就等于把人审门整个删掉。
            if not self.ws.config()["confirm"]["unattended"]:
                raise SkeinError(
                    f"{tid} --unattended 未授权 — 无人值守放行需先 "
                    f"`skein config set confirm.unattended true` (用户显式开一次)")
            return "unattended"
        raise SkeinError(
            f"{tid} 需用户审核规划后才能开工。两条路 (都要真实用户动作):\n"
            f"  ① 看板点击 (最稳): 打开 task 详情, 点「确认规划」按钮\n"
            f"  ② 对话确认: `skein task confirm {tid} --summary` 取摘要 → `AskUserQuestion` 请用户"
            f"批准 → `skein task confirm {tid} --approved`\n"
            f"  🛑 没真问过用户就传 --approved = 伪造审核, 属流程错误\n"
            f"  ⏱ cron/CI 等无人值守场景走 --unattended (需先 config 授权), 别拿 --approved 冒充人审")

    def check(self, a: argparse.Namespace) -> dict[str, Any]:
        # 进行中→检查中: 记 checked 时刻 (board 展示等待/执行时间用)。仅 active 可进检查。
        t = self.ws.store.load(a.id)
        if t["status"] == TaskStatus.CHECK:
            # 幂等: `claim` 已把 task 收进检查中, checker 自跑本命令不该报错 (flow-loop.md §3)
            return {"id": a.id, "status": TaskStatus.CHECK, "idempotent": True}
        if t["status"] != TaskStatus.ACTIVE:
            raise SkeinError(f"{a.id} 状态 {t['status']}, 只有进行中 task 能进检查")
        self.ws._stage_hooks("check", "before", self.ws._hook_ctx(a.id, t=t))
        t["status"] = TaskStatus.CHECK
        t["checked"] = now()
        _timeline.append(t, "task", TaskStatus.CHECK)
        self.ws.store.save(t)
        self.ws._stage_hooks("check", "after", self.ws._hook_ctx(a.id, t=t))
        return {"id": a.id, "status": TaskStatus.CHECK}

    def revert(self, a: argparse.Namespace) -> dict[str, Any]:
        """检查中 → 待处理: check 阶段发现规划有问题, 回退到 plan 重新规划。

        回退销毁 worktree/分支 (与 del 同策略), subtask 状态不动 (规划层面的改动,
        subtask 已做的进度保留, 重新 confirm 后可继续)。checked 时刻保留留痕。
        """
        t = self.ws.store.load(a.id)
        if t["status"] != TaskStatus.CHECK:
            raise SkeinError(f"{a.id} 状态 {t['status']}, 只有检查中 task 能回退到规划")
        self.ws._stage_hooks("revert", "before", self.ws._hook_ctx(a.id, t=t))
        # 销 worktree (check 态已建 worktree, 回退到 pending 需清理)
        destroy_worktrees(t, self.ws.root)
        t["status"] = TaskStatus.PENDING
        t["worktree"] = None
        t["worktrees"] = []
        _timeline.append(t, "task", TaskStatus.PENDING, note="revert: check 回退到 plan")
        self.ws.store.save(t)
        self.ws._stage_hooks("revert", "after", self.ws._hook_ctx(a.id, t=t))
        return {"id": a.id, "status": TaskStatus.PENDING}

    def finishing(self, a: argparse.Namespace) -> dict[str, Any]:
        # 检查中 → 收尾中: 占 gate 槽 (状态∈{检查中,收尾中} 计数, 上限 pools.gate)。
        # 拆成「先占槽标收尾中 → main 派 finisher → finisher 跑 finish 释放槽」两步,
        # 是因为 finisher 是 main 派出去的 agent, 引擎看不见, 限不了并行 finisher 数 —
        # 只能靠这道占槽门间接限制 (design.md §1)。
        t = self.ws.store.load(a.id)
        if t["status"] != TaskStatus.CHECK:
            raise SkeinError(f"{a.id} 状态 {t['status']}, 只能对检查中 task 收尾")
        gate = self.ws.config()["pools"]["gate"]
        occupied = sum(1 for x in self.ws.store.all_tasks()
                       if x["id"] != a.id and x["status"] in (TaskStatus.CHECK, TaskStatus.FINISHING))
        if occupied >= gate:
            raise SkeinError(f"gate 池已满 ({occupied}/{gate}) — 先 finish 一个再收尾")
        self.ws._stage_hooks("finishing", "before", self.ws._hook_ctx(a.id, t=t))
        if not t.get("checked_end"):
            t["checked_end"] = now()
        t["status"] = TaskStatus.FINISHING
        _timeline.append(t, "task", TaskStatus.FINISHING)
        self.ws.store.save(t)
        self.ws._stage_hooks("finishing", "after", self.ws._hook_ctx(a.id, t=t))
        return {"id": a.id, "status": TaskStatus.FINISHING}

    def finish(self, a: argparse.Namespace) -> dict[str, Any]:
        tid = a.id
        t = self.ws.store.load(tid)
        # --force = 看板「强制完成」: 跳过状态门与 gate 池占槽 (门是给自动流程用的), 但下面的
        # 合并 / 销 worktree / 删分支 / 终态落盘一步不少。
        force = bool(getattr(a, "force", False))
        if t["status"] != TaskStatus.FINISHING and not force:
            raise SkeinError(f"{tid} 状态 {t['status']}, 只能 finish 收尾中 task — "
                             f"先 skein task check 再 skein task finishing 占 gate 槽")
        cfg = self.ws.config()
        wts = worktrees_of(t)
        self.ws._stage_hooks("finish", "before", self.ws._hook_ctx(tid, t=t))
        conflicts: list[tuple[str, str]] = []
        for w in wts:
            sub = self.ws.root if w["repo"] == "." else self.ws.root / w["repo"]
            wt = self.ws.root / w["wt"]
            if not w.get("merged"):
                if not wt.exists():
                    raise SkeinError(
                        f"{tid} worktree 缺失 ({w['wt']}) — 无法确认分支 {w['branch']} 已合并"
                    )
                commit_all(wt, f"skein({tid}): {t['name']}")
                m = git("merge", "--no-ff", w["branch"], "-m",
                        f"skein: merge {tid} {t['name']}", cwd=sub, check=False)
                if m.returncode != 0:
                    # 冲突自动解决: 重试 -X theirs (recursive strategy option)。
                    # -X theirs 只在冲突 hunk 上用 worktree 分支版本, 非冲突部分自动三方合并 —
                    # 即 task 产出 (theirs) 覆盖冲突区, main 改动保留在无冲突区。
                    aborted = git("merge", "--abort", cwd=sub, check=False)
                    m2 = git("merge", "--no-ff", "-X", "theirs", w["branch"], "-m",
                             f"skein: merge {tid} {t['name']} (auto theirs)", cwd=sub, check=False)
                    if m2.returncode != 0:
                        detail = m.stdout + m.stderr
                        git("merge", "--abort", cwd=sub, check=False)
                        conflicts.append((w["repo"], detail))
                        continue
                w["merged"] = True
                self.ws.store.save(t)
            if wt.exists():
                removed = git("worktree", "remove", str(wt), "--force", cwd=sub, check=False)
                if removed.returncode != 0:
                    raise SkeinError(
                        f"{tid} worktree 清理失败 ({w['wt']}): "
                        f"{removed.stdout}{removed.stderr}"
                    )
            branch = git("rev-parse", "--verify", f"refs/heads/{w['branch']}",
                         cwd=sub, check=False)
            if branch.returncode == 0:
                deleted = git("branch", "-D", w["branch"], cwd=sub, check=False)
                if deleted.returncode != 0:
                    raise SkeinError(
                        f"{tid} branch 清理失败 ({w['branch']}): "
                        f"{deleted.stdout}{deleted.stderr}"
                    )
        if conflicts:
            t["worktrees"] = wts
            self.ws.store.save(t)
            detail = "\n".join(f"  子 git {r}: 自动 theirs 合并仍失败" for r, _ in conflicts)
            raise SkeinError(
                f"{tid} 部分子 git 合并冲突 (已尝试自动 theirs 仍失败), "
                f"已合并的保留、task 仍 finishing。"
                f"手动解冲突后重跑 finish (幂等跳过已合并):\n{detail}")

        # 先完成 worktree 合并和 finish.after；失败时 task 保持 finishing，可重试。
        self.ws._stage_hooks("finish", "after", self.ws._hook_ctx(tid, t=t))
        t["status"] = TaskStatus.DONE
        t["worktree"] = None
        t["worktrees"] = []
        t["finished"] = now()
        if not t.get("checked_end"):
            t["checked_end"] = now()  # 强制路径没走过 finishing, 补齐检查结束时刻 (看板算耗时用)
        _timeline.append(t, "task", TaskStatus.DONE, note=_FORCE_NOTE if force else "")
        self.ws.store.save(t)
        # commit 必须排在 save 之后: 先 commit 会把 .skein/task.json 的完成态和归档移动
        # 留在工作区外, finish 完仓库仍是脏的 (原地模式实测)。
        if not wts and self.ws.git and cfg.get("auto_commit", True):
            commit_all(self.ws.root, f"skein({tid}): {t['name']}")
        archived = not (self.ws.tasks / tid).exists()
        rest = self.ws.store.active()
        return {"id": tid, "status": TaskStatus.DONE, "archived": archived,
                "remaining": [x["id"] for x in rest]}

    def del_(self, a: argparse.Namespace) -> dict[str, Any]:
        # 删 task (软删 → .skein/trash/<id>.<date>/, 可恢复) 或单 subtask (直接移除, 不进 trash)
        # 无状态门可跳, 故不读 a.force —— CLI 收该 flag 只为与 confirm/finish 的强制语义对齐。
        tid = a.task_id
        src = self.ws.tasks / tid
        if not src.exists() or not (src / "task.json").exists():
            raise SkeinError(f"task 不存在: {tid}")
        t = self.ws.store.load(tid)

        if a.subtask_sid:  # 删单 subtask  # type: ignore[attr-defined]
            sid = a.subtask_sid
            subs = t.get("subtasks", [])
            new_subs = [s for s in subs if s.get("sid") != sid]
            if len(new_subs) == len(subs):
                raise SkeinError(f"subtask 不存在: {tid}/{sid}")
            if a.dry_run:
                return {"dry_run": True, "action": "remove_subtask", "task": tid,
                        "subtask": sid, "remaining": len(new_subs)}
            t["subtasks"] = new_subs
            self.ws.store.save(t)  # save 已渲染子任务看板 + 刷顶层索引
            return {"id": tid, "subtask": sid, "removed": True, "remaining": len(new_subs)}

        if a.dry_run:
            result: dict[str, Any] = {"dry_run": True, "action": "delete_task", "task": tid,
                                       "name": t["name"]}
            if t["status"] in STATUS_INFLIGHT:
                result["worktrees"] = [{"wt": w["wt"], "branch": w["branch"], "repo": w["repo"]}
                                       for w in worktrees_of(t)]
            return result

        # 在途 task (进行中/检查中/收尾中) 先销 worktree/分支 (finish/del 同策略, 免悬挂); 待处理/调研中/done 无 worktree, 跳过
        if t["status"] in STATUS_INFLIGHT:
            destroy_worktrees(t, self.ws.root)
        dst = self.ws.trash(src, tid)
        self.ws.store.sync()  # 刷顶层索引 (移除该 task) + 看板
        return {"id": tid, "deleted": True, "trash_path": str(dst)}

    def rename(self, a: argparse.Namespace) -> dict[str, Any]:
        # 重命名 task/subtask 的 id 或 name (至少给一个 --id / --name)。
        # - 无 sid: 改 task。--name 改显示名 (任意状态); --id 改 id (仅 pending, 同步目录/branch/别 task deps/child parent/顶层索引)
        # - 带 sid: 改 subtask。--name 改子任务名; --id 改 sid (同步同 task 内别 subtask 的 depends_on 引用)
        tid = a.tid
        t = self.ws.store.load(tid)  # 不存在即 SkeinError
        new_id = (a.id or "").strip() or None
        new_name = a.name  # None=不改; "" 视为显式空名 (校验拒空)
        if not new_id and new_name is None:
            raise SkeinError("rename 需至少一个: --id 或 --name")
        if new_name is not None and not new_name.strip():
            raise SkeinError("--name 不可为空")

        if a.sid:  # 改 subtask
            subs = t.get("subtasks", [])
            s = next((x for x in subs if x.get("sid") == a.sid), None)
            if s is None:
                raise SkeinError(f"subtask 不存在: {tid}/{a.sid}")
            if new_id and any(x.get("sid") == new_id for x in subs):
                raise SkeinError(f"sid 已占用: {tid}/{new_id}")
            if new_name is not None:
                s["name"] = new_name
            if new_id:
                old_sid = s["sid"]
                s["sid"] = new_id
                for x in subs:  # 同 task 内别 subtask 的 depends_on 引用同步改名
                    if x is s:
                        continue
                    x["depends_on"] = [new_id if d == old_sid else d for d in x.get("depends_on", [])]
            self.ws.store.save(t)
            return {"task": tid, "subtask": new_id or a.sid,
                    "sid": new_id or a.sid,
                    "name": new_name if new_name is not None else s["name"]}

        # 改 task
        if new_name is not None:
            t["name"] = new_name
        if not new_id:  # 仅改 name
            self.ws.store.save(t)
            return {"id": tid, "name": t["name"]}
        # 改 id: 仅 pre-confirm (待处理/调研中 无 live worktree; active/check/finishing 改 id 需迁分支+移 worktree, 风险高不支持)
        if t["status"] not in (TaskStatus.PENDING, TaskStatus.RESEARCH):
            raise SkeinError(
                f"task id 重命名仅限 confirm 前 (待处理/调研中): {tid} 当前 {t['status']} "
                "(在途 task 有 live worktree/branch, 不支持改 id; 先 finish 或 del, 或只改 --name)")
        if not SLUG_RE.match(new_id):
            raise SkeinError(f"非法 id: {new_id!r} — 须为 kebab-case slug (小写字母/数字/连字符, 字母数字开头)")
        if CODE_ID_RE.match(new_id):
            raise SkeinError(f"id 须可读: {new_id!r} 是字母+数字编号 — 用描述性 slug")
        if new_id in self.ws.store.used_ids():
            raise SkeinError(f"id 已占用: {new_id} — 换一个 (含已归档的也不可复用)")
        old_id = t["id"]
        t["id"] = new_id
        t["branch"] = f"skein/{new_id}"  # pending 无 worktree, 只更 branch 字符串
        # 目录改名 (旧 → 新), 再经 _save 按新 id 落 task.json + 刷子任务看板
        # ponytail: design.md 脚手架内的提示行不重写 (planning 后已被 AI 大改, 属 AI 内容, 非脚本真值)
        shutil.move(str(self.ws.tasks / old_id), str(self.ws.tasks / new_id))
        self.ws.store.save(t, sync_index=False)
        for other in self.ws.store.all_tasks():  # 同步别 task 的 deps 引用
            if other["id"] == new_id:
                continue
            changed = False
            if old_id in (other.get("deps") or []):
                other["deps"] = [new_id if d == old_id else d for d in other["deps"]]
                changed = True
            if changed:
                self.ws.store.save(other, sync_index=False)
        self.ws.store.sync()  # 多 task 落盘后一次刷顶层索引
        return {"old_id": old_id, "new_id": new_id}
