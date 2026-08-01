"""`Lifecycle` — task 状态机: 待处理 → 就绪 → 进行中 → 检查中 → 已完成, 外加删/改名。

## 这个类的边界
只管**一个 task 自身的状态迁移与计划字段** (deps/estimate/repos)。不碰调度 (归 `Scheduler`)、
不碰只读投影 (归 `Query`)、不碰 prd/契约正文 (归 `Artifacts`)、不碰工作区级命令 (归 `Admin`)。

## 依赖为什么是构造入参
`ws` 给路径/配置/落盘/钩子, `doctor` 给 start 前置体检 —— 后者本来是 `DoctorMixin` 挂在门面
上的方法, 这里只要"能跑一次体检"这个能力, 不需要认识整个门面。注入一个可调用对象, 依赖就到此
为止, 不会顺着 `self` 摸到别的东西。
"""
from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from skeinlib.workspace import Workspace

from skeinlib.dag import _sub_estimate_sum
from skeinlib.errors import SkeinError
from skeinlib.model import (CODE_ID_RE, PRIORITY_DEFAULT, SLUG_RE, STATUS_INFLIGHT, S_ACTIVE, S_CHECK,
                            S_DONE, S_PENDING, S_READY, now)
from skeinlib.prd import review_summary, validate_prd, validate_seam
from skeinlib.priority import validate_priority
from skeinlib.worktree import commit_all, destroy_worktrees, git, make_worktree, parse_repos, worktrees_of

import datetime
import json
import shutil
import sys
from typing import Callable, Optional


class Lifecycle:
    """task 状态机 + 计划字段编辑。"""

    def __init__(self, ws: "Workspace", doctor: Callable[[argparse.Namespace], Any]) -> None:
        self.ws = ws
        self._doctor = doctor

    # 下面这些是从 Skein 搬过来的方法体, 原样保留 —— 只把 self.X 改成 self.ws.X (见文件末尾说明)。
    def create(self, a: argparse.Namespace) -> None:
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
        # task 级父子层校验 (限 2 层: supertask→task→subtask)
        parent_id = (a.parent or "").strip() or None
        kind = a.kind or "task"
        if kind == "supertask" and parent_id:
            raise SkeinError(f"supertask 不可有 parent (supertask 是顶层父聚合层) — 去掉 --parent {parent_id}")
        if parent_id:
            p = self.ws.store.load(parent_id)  # _load 不存在 → SkeinError「task 不存在」(parent 引用完整性)
            if p.get("parent"):
                # 被引用的 parent 自身是 child (其 parent != None) → 拒, 禁 child 作父, 深度超 2 层
                raise SkeinError(
                    f"深度超限: parent {parent_id} 本身是 child (其 parent={p.get('parent')!r}) — "
                    f"supertask 不可再嵌套 supertask (限 2 层: supertask→task→subtask)")
            # 父是 supertask, 或是独立 task (kind=task 且 parent=None, 允许升格作聚合父 — 但更
            # 规范的做法是显式 supertask): 都放行。深度已由上面那道 parent 链检查兜住。
            # ponytail: 不强制要求父必须 supertask, 只要 parent 链不超 2 层 (parent 的 parent=None 即可)
            if p.get("kind") not in ("supertask", None, "task"):
                raise SkeinError(f"parent {parent_id} kind={p.get('kind')!r} 非法 — 仅允许 task|supertask")
        repos = parse_repos(getattr(a, "repos", None))
        if repos and not self.ws.config()["worktree"]["enabled"]:
            raise SkeinError(f"{tid} 声明 --repos 但 config worktree.enabled=false — 多子 git 隔离需启用 worktree")
        self.ws._stage_hooks("create", "before", self.ws._hook_ctx(tid))
        (self.ws.tasks / tid).mkdir(parents=True)
        self._scaffold(tid, a.name)  # 落 prd/design/findings 脚手架 (planning 填)
        deps = [d.strip() for d in (a.deps or "").split(",") if d.strip()]
        t = {
            "id": tid, "name": a.name, "desc": a.desc,
            "status": S_PENDING, "deps": deps, "contracts": [], "subtasks": [],
            "priority": validate_priority(getattr(a, "priority", None)),  # 四档枚举, 未指定落中档
            "estimate": getattr(a, "estimate", None),  # 预计工时(小时), plan 阶段必填, confirm 硬门校验
            "repos": repos,          # planning 声明的目标子 git (rel 路径; 空=单根/原地模式)
            "worktree": None, "worktrees": [], "branch": f"skein/{tid}",
            "parent": parent_id,     # 父 supertask id; None=独立 task (create 默认; --parent 指向 supertask)
            "kind": kind,            # "task"(普通/独立, 默认) | "supertask"(父聚合层)
            "created": now(),        # 创建时刻
            "started": None,         # exec 时刻 (start 时置)
            "confirmed": None,       # 就绪时刻 (confirm 命令置)
            "checked": None,         # 进入检查阶段时刻 (check 命令置)
            "finished": None,        # 完成时刻 (finish 时置; 保留期从此计)
            "updated": now(),
        }
        self.ws.store.save(t)  # _save 已渲染子任务看板
        self.ws.store.sync()  # 刷新顶层 tasks 索引 + 看板 + html
        self.ws._stage_hooks("create", "after", self.ws._hook_ctx(tid, t=t))
        print(f"{tid}\t{self.ws.tasks / tid}")

    def _scaffold(self, tid: str, name: str) -> None:
        """落 planning 双工件脚手架 (prd 主入口 / design 详细设计).
        findings.md 不预建 — 仅真调研时由 skein-researcher 边研边增量生成 (无调研不产出)。
        模板极简 (只给骨架标题, 正文 planning 填), 避免占 token; 已存在则不覆盖。
        调度 DAG / 子任务不在此 — 归 task.json (脚本维护)。"""
        d = self.ws.tasks / tid
        files = {
            "prd.md": (
                f"# {name} — PRD (主入口)\n\n"
                "> 禁写具体文件路径与代码片段 (会很快过期) —— 例外: prototype 产出的能精确编码决策的片段 "
                "(状态机/schema/type shape) 可内联, 且须注明来自 prototype。\n\n"
                "## 目标\n要解决什么 / 用户价值 / 成功长什么样:\n- [ ] TODO: 填目标\n\n"
                "## 边界\n范围内 / 范围外 (非目标) / 已知约束:\n- [ ] TODO: 填边界\n\n"
                "## User Stories\n"
                "极其详尽地穷举, 覆盖功能各方面 (含边界情况) —— 穷举本身就是逼出边界情况的机械手段:\n"
                "1. As a <actor>, I want <feature>, so that <benefit>\n\n"
                "## 验收标准\n可执行、可核对的完成断言 (逐条):\n- [ ] TODO: 填验收标准\n\n"
                "## Testing Decisions\n"
                "什么算好测试 (只测外部行为不测实现细节) / 测哪些模块 / codebase 内的同类测试先例:\n"
                "- [ ] TODO: 填 Testing Decisions\n\n"
                "## 索引\n- 详细设计: [design.md](design.md)\n"
                "- 调研收敛: [findings.md](findings.md) (仅真调研时生)\n"
                "- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list " + tid + "`)\n"),
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

    def repos(self, a: argparse.Namespace) -> None:
        # 查/声明 task 的目标子 git (planning 声明: 每个各开 worktree)。仅 pending 可改 (start 后 worktree 已定)
        t = self.ws.store.load(a.id)
        if a.set is None:
            print("\n".join(t.get("repos") or []) or "(未声明子 git — 单根/原地模式)")
            return
        if not self.ws.config()["worktree"]["enabled"]:
            raise SkeinError(f"{a.id} config worktree.enabled=false — worktree 禁用, 不可声明 repos")
        if t["status"] not in (S_PENDING, S_READY):
            raise SkeinError(f"{a.id} 状态 {t['status']}, repos 只能在 start 前 (待处理/就绪) 声明")
        t["repos"] = parse_repos(a.set)
        self.ws.store.save(t)
        self.ws.store.sync()
        print(f"{a.id} repos = {', '.join(t['repos']) or '(空)'}")

    def estimate(self, a: argparse.Namespace) -> None:
        # 查/填 task 预计工时(小时)。plan 阶段必填, confirm 硬门校验 (见 _validate_estimate)。
        # 仅 pending/ready 可改 (start 后执行已启动, 工时估算不再变更调度)。
        t = self.ws.store.load(a.id)
        if a.set is None:
            est = t.get("estimate")
            subsum = _sub_estimate_sum(t)
            print(f"{est} h" if est else "(未估算)")
            if subsum:
                print(f"  subtask 合计 {subsum} h + plan/check 自身开销 "
                      f"{round((est or 0) - subsum, 2)} h")
            return
        if t["status"] not in (S_PENDING, S_READY):
            raise SkeinError(f"{a.id} 状态 {t['status']}, estimate 只能在 start 前 (待处理/就绪) 设置")
        try:
            val = float(a.set)
        except ValueError:
            raise SkeinError(f"预计工时须为数字(小时): {a.set!r}")
        if val <= 0:
            raise SkeinError(f"预计工时须为正数: {val}")
        t["estimate"] = val
        self.ws.store.save(t)
        self.ws.store.sync()
        print(f"{a.id} estimate = {val} h")

    def priority(self, a: argparse.Namespace) -> None:
        # 查/改 task 优先级。调度旋钮而非规划契约 (design.md) — 不锁状态, 任意状态均可改;
        # 只改字段不碰执行中的槽, 故「不打断已在跑的」是结构性成立, 不需要额外校验。
        t = self.ws.store.load(a.id)
        if a.set is None:
            print(t.get("priority") or PRIORITY_DEFAULT)
            return
        t["priority"] = validate_priority(a.set)
        self.ws.store.save(t)
        self.ws.store.sync()
        print(f"{a.id} priority = {t['priority']}")

    def deps(self, a: argparse.Namespace) -> None:
        # 查/补 task 级前置 DAG (dedup 排序用: 给散落 task 之间补执行序, 织成完整 DAG)。
        # 仅 pending 可改 (start 后调度已定); 且仅当现有 deps 为空才允许写 —
        # dedup 只对无依赖的 task 补新序, 既有依赖一律不碰 (防覆盖人工/plan 声明的前置)。
        t = self.ws.store.load(a.id)
        if a.set is None:
            print(",".join(t.get("deps") or []) or "(无前置)")
            return
        if t["status"] not in (S_PENDING, S_READY):
            raise SkeinError(f"{a.id} 状态 {t['status']}, deps 只能在 start 前 (待处理/就绪) 设置")
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
        WHITE, GRAY = 0, 1
        color: dict[str, int] = {}
        stack: list[str] = []
        def dfs(n: str) -> Optional[list[str]]:
            color[n] = GRAY; stack.append(n)
            for m in graph.get(n, []):
                if color.get(m) == GRAY:
                    return stack[stack.index(m):] + [m]
                if color.get(m, WHITE) == WHITE:
                    r = dfs(m)
                    if r:
                        return r
            color[n] = 2; stack.pop()
            return None
        for n in graph:
            if color.get(n, WHITE) == WHITE:
                c = dfs(n)
                if c:
                    raise SkeinError(f"deps 成环: {' -> '.join(c)}")
        t["deps"] = new
        self.ws.store.save(t)
        self.ws.store.sync()
        print(f"{a.id} deps = {', '.join(new) or '(空)'}")

    def _validate_estimate(self, tid: str, t: dict[str, Any]) -> None:
        # confirm 硬门: 预计工时(小时)必须已填且为正数, 缺失/默认空 → 拒绝进就绪。
        # 且须自下而上累加: task 工时 ≥ Σ subtask 工时 (差额 = plan/check 等 task 自身开销),
        # 低于合计说明整体拍脑袋而非按实际要做的事逐项估。规则详见 estimate-gate.md。
        est = t.get("estimate")
        if est is None or est == "" or not (isinstance(est, (int, float)) and est > 0):
            raise SkeinError(
                f"{tid} 预计工时未填 — 先 `skein estimate {tid} --set <小时数>` 填实再 confirm")
        subsum = _sub_estimate_sum(t)
        if subsum and est < subsum:
            raise SkeinError(
                f"{tid} 预计工时 {est} h 低于 subtask 合计 {subsum} h — "
                f"task 工时须 ≥ Σ subtask + plan/check 自身开销, "
                f"`skein estimate {tid} --set <≥{subsum}>`")

    def confirm(self, a: argparse.Namespace) -> None:
        # 用户确认门 (待处理→就绪): planning 完成 (prd 填齐 + ≥1 subtask + 预计工时) 且用户评审通过后调用,
        # 把 task 从「规划中」推到「就绪」(待启动)。就绪不占并发槽, 供 start 前排队。
        t = self.ws.store.load(a.id)
        if t["status"] != S_PENDING:
            raise SkeinError(f"{a.id} 状态为 {t['status']}, 只能 confirm 待处理 (规划中) task")
        # planning 完成门: 无 subtask / prd 未填齐 / 预计工时未填 → 拒绝进就绪 (逼先补全规划)
        subs = t.get("subtasks") or []
        if len(subs) == 0:
            raise SkeinError(f"{a.id} 无 subtask 登记 — 先 skein subtask add 拆分再 confirm")
        validate_prd(self.ws.tasks, a.id)
        validate_seam(self.ws.tasks, a.id)
        self._validate_estimate(a.id, t)
        if getattr(a, "summary", False):
            # 只出摘要不改状态 — main 拿它塞进 AskUserQuestion。放在结构门之后: 结构不全时
            # 该先报缺什么, 而不是让用户去审一份残缺的 PRD。
            print(review_summary(self.ws.tasks, a.id, t))
            return
        channel = self._require_user_review(a.id, bool(getattr(a, "approved", False)))
        self.ws._stage_hooks("confirm", "before", self.ws._hook_ctx(a.id, t=t))
        t["status"] = S_READY
        t["confirmed"] = now()
        t["confirmed_by"] = channel  # 审核渠道留痕: ask (AskUserQuestion) / user-tty (终端交互)
        self.ws.store.save(t)
        self.ws.store.sync()
        self.ws._stage_hooks("confirm", "after", self.ws._hook_ctx(a.id, t=t))
        print(f"{a.id} 就绪 (规划完成, 待 skein start 启动)")

    # ---- 人审门 (待处理→就绪 的最后一道) ----
    def _require_user_review(self, tid: str, approved: bool) -> str:
        """PRD 必须经用户过目才允许进就绪。返回审核渠道 (写进 `confirmed_by`)。

        ## 为什么要有这道门
        前面三道 (prd 填齐 / ≥1 subtask / 预计工时) 校验的都是**结构**, AI 自己就能填满然后
        自己跑 confirm —— 于是「用户确认门」名存实亡, 一个没人看过的 PRD 直接进了就绪。

        ## 🛑 本方法禁读 stdin
        CLI 的定位是被 skill / agent 调用的, **任何交互都会把调用方挂住** (等一个永远不来的
        输入)。曾经这里有一段 TTY 交互 (打印摘要 + 等用户敲 task id), 已整段删除。审核结果只
        以 `--approved` 这一个布尔量进来, 怎么拿到批准是调用方的事。

        ## 两条合法来源 (都是真实用户动作)
        | 来源 | 怎么走 |
        |---|---|
        | 看板点击 | 用户在 task 详情面板/详情页点「确认规划」→ `POST /__skein__/exec` 白名单转 `confirm <id> --approved`。**AI 没有浏览器, 点不了** |
        | 对话确认 | main 先 `confirm <id> --summary` 取摘要 → `AskUserQuestion` 请用户批准 → 带 `--approved` 再跑 |

        前者 AI 物理上做不到, 后者靠流程纪律 (`AskUserQuestion` 的答案 AI 伪造不了, 但"有没有
        真的问"这一步得 main 自觉) —— 与「有没有真的派 agent」同级。
        """
        if approved:
            return "user"
        raise SkeinError(
            f"{tid} 需用户审核 PRD 后才能进就绪。两条路 (都要真实用户动作):\n"
            f"  ① 看板点击 (最稳): 打开 task 详情, 点「确认规划」按钮\n"
            f"  ② 对话确认: `skein confirm {tid} --summary` 取摘要 → `AskUserQuestion` 请用户"
            f"批准 → `skein confirm {tid} --approved`\n"
            f"  🛑 没真问过用户就传 --approved = 伪造审核, 属流程错误")

    def start(self, a: argparse.Namespace) -> None:
        self._start_task(a.id, a)

    def _start_task(self, tid: str, a: argparse.Namespace, *, quiet: bool = False) -> dict[str, Any]:
        """就绪 → 进行中: 体检 + 并发校验 + 建 worktree + 打时间戳。返回启动后的 task。

        抽成方法是为了给**自动启动**复用 —— `claim exec` / `subtask start` 认领到一个属于「就绪」
        task 的 subtask 时会调它 (见 `_ensure_task_active`), 那条路必须走**完全相同**的副作用:
        doctor 前置体检、task 级 max_active 校验、prd double-check、worktree 建立、started
        时间戳、start 的 before/after 阶段钩子。少任何一样, 自动启动的 task 就与手工 start 的
        不是同一种状态 —— 那类差异极难查 (表现是「有的 task 没 worktree」)。

        `quiet=True` 只压掉给人看的输出, 不跳过任何校验。
        """
        # start 前置体检: 跑 doctor 结构不变量检查, 有 ✗ 错误 → doctor 内 raise SkeinError 阻止 start
        if not quiet:
            print("start 前置体检 (doctor):")
        self._doctor(a)
        t = self.ws.store.load(tid)
        if t["status"] != S_READY:
            raise SkeinError(
                f"{tid} 状态为 {t['status']}, 只能 start 就绪 task — "
                f"待处理(规划中) 须先 skein confirm 过用户确认门")
        cfg = self.ws.config()
        active = self.ws.store.active()
        if len(active) >= cfg["max_active"]:
            raise SkeinError(
                f"task 级并发上限 {cfg['max_active']} (当前 active: "
                f"{', '.join(x['id'] for x in active)}), 先 finish 一个再 start")
        undone = [d for d in t["deps"] if self.ws._dep_unfinished(d)]
        if undone:
            raise SkeinError(f"前置未完成: {', '.join(undone)} — 先 finish 它们")
        # planning 完成门 (subtask + prd) 已在 confirm 时校验; 此处 double-check prd 防 confirm 后被改空
        validate_prd(self.ws.tasks, tid)
        self.ws._stage_hooks("start", "before", self.ws._hook_ctx(tid, t=t))
        t["status"] = S_ACTIVE
        repos = t.get("repos") or []
        wt_cfg = cfg["worktree"]["enabled"]
        wt_on = self.ws.git and wt_cfg  # 单根 worktree: 需根仓是 git; 配置禁用→原地执行
        # --repos 的 git 性由 _mkwt 逐子仓校验 (worktree 落各子仓内), 与父目录是否 git 无关 —
        # 故只在 config 显式禁用时挡, 不吃 self.ws.git (支持非 git 父 + 多 git 子的微服务布局)。
        if repos and not wt_cfg:
            raise SkeinError(
                f"{tid} 声明了 --repos 但 config worktree.enabled=false — 多子 git 隔离需启用 worktree")
        if repos:
            # 多子 git: planning 声明的每个子 git 各开 worktree+branch (并列 repo / submodule 同理)
            t["worktrees"] = [make_worktree(t, r, cfg, self.ws.root) for r in repos]
            t["worktree"] = ", ".join(w["wt"] for w in t["worktrees"])  # 显示汇总
        elif wt_on:
            rel = f"{cfg['worktree']['root']}/skein-{tid}"  # 相对 project root 存盘, 免机器绝对路径入库
            git("worktree", "add", "-b", t["branch"], str(self.ws.root / rel), "HEAD", cwd=self.ws.root)
            t["worktree"] = rel
            t["worktrees"] = [{"repo": ".", "wt": rel, "branch": t["branch"], "merged": False}]
        else:
            t["worktree"] = None  # 非 git / config 禁用, 无 repos: 原地执行, 无 worktree 隔离
            t["worktrees"] = []
        if not t.get("started"):
            t["started"] = now()  # exec 时刻 (首次 start; 重启不覆盖)
        self.ws.store.save(t)
        self.ws.store.sync()
        if t["worktrees"]:
            loc = "\n".join(f"worktree: {w['wt']} (子 git: {w['repo']}, branch: {w['branch']})"
                            for w in t["worktrees"])
        else:
            reason = "config worktree.enabled=false" if self.ws.git else "非 git 仓库"
            loc = f"{reason}: 原地执行 (无 worktree 隔离)"
        self.ws._stage_hooks("start", "after", self.ws._hook_ctx(tid, t=t))
        if not quiet:
            print(f"{tid} started\n{loc}")
        return t

    def check(self, a: argparse.Namespace) -> None:
        # 进行中→检查中: 记 checked 时刻 (board 展示等待/执行时间用)。仅 active 可进检查。
        t = self.ws.store.load(a.id)
        if t["status"] != S_ACTIVE:
            raise SkeinError(f"{a.id} 状态 {t['status']}, 只有进行中 task 能进检查")
        self.ws._stage_hooks("check", "before", self.ws._hook_ctx(a.id, t=t))
        t["status"] = S_CHECK
        t["checked"] = now()
        self.ws.store.save(t)
        self.ws.store.sync()
        self.ws._stage_hooks("check", "after", self.ws._hook_ctx(a.id, t=t))
        print(f"{a.id} checked")

    def finish(self, a: argparse.Namespace) -> None:
        tid = a.id
        t = self.ws.store.load(tid)
        if t["status"] not in STATUS_INFLIGHT:
            raise SkeinError(f"{tid} 状态 {t['status']}, 非在途 (进行中/检查中) 无法 finish")
        # supertask 聚合归档: finish 前所有 child task(parent 指向它)须全 done
        # ponytail: 遍历 tasks 过滤 parent==tid 找 child (不维护 child_ids 数组, 真值源单一)
        if t.get("kind") == "supertask":
            pending = [c["id"] for c in self.ws.store.all_tasks() if c.get("parent") == tid and c["status"] != S_DONE]
            if pending:
                raise SkeinError(
                    f"{tid} 是 supertask, 仍有未完成 child task: {', '.join(pending)} — "
                    f"先 finish 全部 child 再 finish super (聚合归档要求 child 全 done)")
        cfg = self.ws.config()
        wts = worktrees_of(t)
        self.ws._stage_hooks("finish", "before", self.ws._hook_ctx(tid, t=t))
        conflicts: list[tuple[str, str]] = []  # [(repo, 冲突输出)] — 部分子 git 冲突时保留已合并进度, task 留 active 供幂等重跑
        for w in wts:
            if w.get("merged"):
                continue  # 幂等: 前次已合并的子 git 跳过 (部分冲突重跑场景)
            sub = self.ws.root if w["repo"] == "." else self.ws.root / w["repo"]  # merge 落各子 git
            wt = self.ws.root / w["wt"]
            if not wt.exists():
                sys.stderr.write(
                    f"{tid} worktree 缺失 ({w['wt']}) — 跳过, 分支 {w['branch']} 若有提交未并入\n")
                w["merged"] = True  # 缺失即无从合并, 标记免卡住
                continue
            # worktree 场景强制 commit, 不看 auto_commit — 未提交改动 merge 不进主干,
            # 且下面 worktree remove --force 会连同丢弃 (auto_commit 只管原地模式, 见 finish 末尾)
            commit_all(wt, f"skein({tid}): {t['name']}")
            # 合并回该子 git 的主工作区
            m = git("merge", "--no-ff", w["branch"], "-m",
                    f"skein: merge {tid} {t['name']}", cwd=sub, check=False)
            if m.returncode != 0:
                git("merge", "--abort", cwd=sub, check=False)
                conflicts.append((w["repo"], m.stdout + m.stderr))
                continue
            git("worktree", "remove", str(wt), "--force", cwd=sub, check=False)
            git("branch", "-D", w["branch"], cwd=sub, check=False)
            w["merged"] = True
        if conflicts:
            # 保存已合并进度 (worktrees 各 merged 标记), task 仍 active — 解冲突后重跑 finish 只补未合并子 git
            t["worktrees"] = wts
            self.ws.store.save(t)
            self.ws.store.sync()
            detail = "\n".join(f"  子 git {r}: 冲突已 abort" for r, _ in conflicts)
            raise SkeinError(
                f"{tid} 部分子 git 合并冲突, 已合并的保留、task 仍 active。"
                f"解冲突后重跑 finish (幂等跳过已合并):\n{detail}")
        t["status"] = S_DONE
        t["worktree"] = None
        t["worktrees"] = []
        t["finished"] = now()  # 完成时刻 — 保留期从此计, 超 retain_days 由 _autoclean 归档
        self.ws.store.save(t)
        self.ws.store.sync()  # 重写顶层索引 (完成 task 仍留看板; retain_days=0 时 _autoclean 即归档)
        archived = not (self.ws.tasks / tid).exists()  # retain_days<=0 → 已被 _autoclean 归档
        # 原地模式 (无 worktree): 此时才轮到 auto_commit 决定提不提交; 关则改动留工作区由用户自管。
        # 放在 _save/_sync 之后 — 连同 .skein 状态一起提交, 免留下脏索引
        if not wts and self.ws.git and cfg.get("auto_commit", True):
            commit_all(self.ws.root, f"skein({tid}): {t['name']}")
        cfg = self.ws.config()
        rest = self.ws.store.active()
        tail = (f", 剩余 active: {', '.join(x['id'] for x in rest)}" if rest else ", 无剩余 active")
        keep = "已归档" if archived else f"保留 {cfg.get('retain_days', 7)} 天后自动归档"
        self.ws._stage_hooks("finish", "after", self.ws._hook_ctx(tid, t=t))
        print(f"{tid} finished ({keep})" + tail)

    def archive(self, a: argparse.Namespace) -> None:
        # 归档 = 丢弃 (不 merge): 先销 worktree/branch, 免残留悬挂
        f = self.ws.tasks / a.id / "task.json"
        t = json.loads(f.read_text()) if f.exists() else None
        self.ws._stage_hooks("archive", "before", self.ws._hook_ctx(a.id, t=t))
        if t is not None:
            for w in worktrees_of(t):
                sub = self.ws.root if w["repo"] == "." else self.ws.root / w["repo"]
                wt = self.ws.root / w["wt"]
                if wt.exists():
                    git("worktree", "remove", str(wt), "--force", cwd=sub, check=False)
                git("branch", "-D", w["branch"], cwd=sub, check=False)
        self.ws.store.archive_task(a.id)
        self.ws.store.sync()  # 重写顶层 tasks 索引 (去掉已归档 task)
        self.ws._stage_hooks("archive", "after", self.ws._hook_ctx(a.id, t=t))
        print(f"{a.id} archived")

    def del_(self, a: argparse.Namespace) -> None:
        # 删 task (软删 → .skein/trash/<id>.<date>/, 可恢复) 或单 subtask (直接移除, 不进 trash)
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
                print(f"[dry-run] 将从 {tid} 移除 subtask {sid} (task 目录与其余 subtask 不动)")
                return
            t["subtasks"] = new_subs
            self.ws.store.save(t)  # _save 渲染子任务看板
            self.ws.store.sync()   # 刷顶层索引 + 看板
            print(f"{tid}/{sid} removed ({len(new_subs)} subtask 剩余)")
            return

        if a.dry_run:
            lines = [f"[dry-run] 将删 task {tid} ({t['name']}):",
                     f"  软删: {src} → {self.ws.trash_dir}/{tid}.{datetime.datetime.now().strftime('%Y%m%d')}/"]
            if t["status"] in STATUS_INFLIGHT:
                for w in worktrees_of(t):
                    lines.append(f"  销 worktree: {w['wt']}  分支: {w['branch']}  (子 git {w['repo']})")
            print("\n".join(lines))
            return

        # 在途 task (进行中/检查中) 先销 worktree/分支 (finish/archive 同策略, 免悬挂); 待处理/就绪/done 无 worktree, 跳过
        if t["status"] in STATUS_INFLIGHT:
            destroy_worktrees(t, self.ws.root)
        dst = self.ws.trash_dir / f"{tid}.{datetime.datetime.now().strftime('%Y%m%d')}"
        self.ws.trash_dir.mkdir(parents=True, exist_ok=True)
        if dst.exists():  # 同日重复删同 id → 先清旧 (同名目录 shutil.move 跨平台行为不一)
            shutil.rmtree(dst)
        shutil.move(str(src), str(dst))
        self.ws.store.sync()  # 刷顶层索引 (移除该 task) + 看板
        print(f"{tid} deleted (软删可恢复: {dst})")

    def rename(self, a: argparse.Namespace) -> None:
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
            self.ws.store.sync()
            print(f"{tid}/{a.sid} renamed"
                  + (f" → sid={new_id}" if new_id else "")
                  + (f" name={new_name!r}" if new_name is not None else ""))
            return

        # 改 task
        if new_name is not None:
            t["name"] = new_name
        if not new_id:  # 仅改 name
            self.ws.store.save(t)
            self.ws.store.sync()
            print(f"{tid} renamed: name={t['name']!r}")
            return
        # 改 id: 仅 pre-start (待处理/就绪 无 live worktree; active/check 改 id 需迁分支+移 worktree, 风险高不支持)
        if t["status"] not in (S_PENDING, S_READY):
            raise SkeinError(
                f"task id 重命名仅限 start 前 (待处理/就绪): {tid} 当前 {t['status']} "
                "(在途 task 有 live worktree/branch, 不支持改 id; 先 finish/archive, 或只改 --name)")
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
        # ponytail: prd.md 脚手架内的 `subtask list <old-id>` 提示行不重写 (planning 后 prd 已被 AI 大改, 属 AI 内容, 非脚本真值)
        shutil.move(str(self.ws.tasks / old_id), str(self.ws.tasks / new_id))
        self.ws.store.save(t)
        for other in self.ws.store.all_tasks():  # 同步别 task 的 deps + child 的 parent 引用
            if other["id"] == new_id:
                continue
            changed = False
            if old_id in (other.get("deps") or []):
                other["deps"] = [new_id if d == old_id else d for d in other["deps"]]
                changed = True
            if other.get("parent") == old_id:
                other["parent"] = new_id
                changed = True
            if changed:
                self.ws.store.save(other)
        self.ws.store.sync()
        print(f"{old_id} renamed → {new_id}")
