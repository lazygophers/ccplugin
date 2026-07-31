"""`Skein` — 命令面: 全部状态迁移子命令 (create/confirm/start/check/finish/archive/subtask/...)。

## 这个类还剩什么
落盘归 `store.TaskStore`, 渲染归 `board`, 视图归 `views`, http 归 `serve`+`boardsource`,
体检归 `doctor`, worktree/prd/migrate/config 各有其文件。这里只剩**状态迁移的业务规则**:
什么状态能进什么状态、各阶段的硬门、DAG 就绪判定与 subtask 调度。

`DoctorMixin` / `BoardSourceMixin` 两个 mixin 把体检与 DataSource 实现挂回来 —— 它们要读同
一批 `self` 属性, 见各自文件顶部的「依赖契约」。

## 工作区写锁
`_workspace_lock` 是 fcntl.flock 排他锁, 由 `cli.main` 对会写盘的命令统一加, 命令自身不管锁。
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterator, Optional, cast

from skeinlib.hooks.runner import DBG, HookBlocked, _run_hooks
from skeinlib.config import (_CFG_LEGACY, CONFIG_DEFAULTS,
                             HOOKS_SKELETON,
                             _cfg_backfill, _cfg_effective, _cfg_get_path,
                             _cfg_paths, _cfg_set_path, _coerce_config, _yaml_dump,
                             _yaml_load, hooks_schema_errors)
from skeinlib.paths import SPEC_ENTRY
from skeinlib.boardsource import BoardSourceMixin
from skeinlib.dag import (_crit_weight, _split, _split_semi,
                          _sub_estimate_sum, _sub_pct, _task_pct)
from skeinlib.doctor import DoctorMixin
from skeinlib.errors import SkeinError
from skeinlib.migrate import (disable_trellisx_plugin, migrate_trellis_tasks,
                              purge_trellis_hooks, purge_wiring, settings_trellis_notes)
from skeinlib.prd import (review_summary, section_add, section_check, section_read,
                          section_write, validate_prd, validate_seam)
from skeinlib.store import TaskStore
from skeinlib.model import (CODE_ID_RE, PRD_SECTIONS_V4,
                            PRD_SECTIONS_V6, PRD_TYPE_ALIAS, SLUG_RE,
                            SS_DONE, SS_FAILED, SS_PENDING, SS_RUNNING, STATUS_INFLIGHT, S_ACTIVE, S_CHECK, S_DONE,
                            S_PENDING, S_READY, _STATUS_ALIAS, now)
from skeinlib.views import (_fmt_ts,
                            )
from skeinlib.worktree import (commit_all, destroy_worktrees, git,
                               ignore_worktree_dir, make_worktree, parse_repos, worktrees_of)




# 插件无法直接发货 settings.json 的 env 块 (plugin.json 无 env 字段)。
# 官方持久化 env 的机制: SessionStart hook 往 $CLAUDE_ENV_FILE 追加 export。
# 这样这些 env 随 skein 插件的 SessionStart hook 一起发货, 不落用户项目 settings。
_ENV_EXPORTS = (
    "export CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1",
    # skein 调度只用单 subagent (skein subtask + 单 Agent 调用), 禁 agent-teams 防误升级到 team。
    # CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=0 = 显式关闭 (官方 docs/en/agent-teams: 默认即关, 此为冗余保障)。
    "export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=0",
)


def _persist_bash_cwd_env() -> None:
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if not env_file:
        return  # 非 SessionStart/Setup/CwdChanged/FileChanged 事件时不可用, 静默跳过
    try:
        p = Path(env_file)
        existing = p.read_text() if p.exists() else ""
        missing = [e for e in _ENV_EXPORTS if e not in existing]  # 幂等: 逐条查, 已写的不重复
        if missing:
            with p.open("a") as f:
                f.write("\n".join(missing) + "\n")
    except OSError:
        pass  # env 持久化尽力而为, 失败不阻断 session-context 主流程


@contextlib.contextmanager
def _workspace_lock(lock_path: Path, timeout: float = 10.0, poll: float = 0.05) -> Iterator[None]:
    # 工作区级排他写锁 (fcntl.flock): 防多 skein 进程并发 read-modify-write 破坏 task.json。
    # 阻塞等待锁释放, 超 timeout 秒仍拿不到 → SkeinError (非死等)。CLI 短命, 全局锁足够。
    # ponytail: global lock, per-task locks if throughput matters.
    # config-hooks: SKEIN_IN_HOOK 已置位 = 本进程是钩子(before/after)里派生的嵌套 skein 调用,
    # 其父进程正是本锁的持有者且仍在临界区内(阶段命令body含钩子执行)——同进程链单写者,
    # 再抢同一把锁必死锁到 timeout。跳过加锁(整个 with 块变 no-op), 写序仍由外层锁串行化。
    if os.environ.get("SKEIN_IN_HOOK"):
        yield
        return
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    f = open(lock_path, "w")
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise SkeinError(
                        f"获取 .skein 写锁超时 ({timeout}s) — 另一 skein 进程持锁未释放: {lock_path}")
                time.sleep(poll)
        DBG.log(f"🔒 已获工作区写锁 {lock_path}", style="dim")
        yield
    finally:
        f.close()  # 关闭即释放 flock
        DBG.log("🔓 释放工作区写锁", style="dim")


































# config-hooks/c3b: `hooks` 键刻意不进 CONFIG_DEFAULTS —— 可选特性, init 不写、config 展示不含,
# 代码一律 cfg.get("hooks") 缺失即 no-op (见 hooks.py _agent_hook)。安全副产品: /__skein__/config
# 写端点(下方 _cfg_save)只回填本字典已列举的叶, hooks 键天然被忽略, 免专写排除逻辑防「远程写 shell = RCE」。

# 执行器 (hooks.runner._run_hooks) 也从不读它, 强制填一个零信息量的字段纯属样板; 写了就校验, 不写按
# command 处理。与 docs/hooks.md 的示例 (`- command: "npm run lint"`) 一致。





















class Skein(DoctorMixin, BoardSourceMixin):
    # task/subtask 记录用 dict[str, Any] (JSON 落盘 schema, 字段异质)
    def __init__(self) -> None:
        # git 非强制: 在 git 仓库内则用其根 + 启用 worktree 隔离; 否则用 cwd 原地执行
        # (微服务/前后端分离: cwd 无 git, 子目录各自独立仓库 — 正是最需要不挡 git 的场景)。
        r = git("rev-parse", "--show-toplevel", check=False)
        self.git: bool = r.returncode == 0
        self.root: Path = Path(r.stdout.strip()) if self.git else Path.cwd()
        self.dir: Path = self.root / ".skein"
        self.tasks: Path = self.dir / "task"
        self.archive_dir: Path = self.tasks / "archive"
        self.trash_dir: Path = self.dir / "trash"  # 软删 task 落此 (.skein/trash/<id>.<YYYYMMDD>/, 可恢复; 在 task/ 外, 免被 _all/doctor 扫到)
        # 看板 title/标题带项目名, 用户一眼知是哪个项目
        self.proj: str = self.root.name
        # 落盘层: task.json 唯一写入口。config / worktree 列展示两个依赖注入进去,
        # 这样 store 不认识 commands 层, 依赖单向 (见 skeinlib/store.py)。
        self.store = TaskStore(self.dir, self.tasks, self.archive_dir,
                               self.config, self._wt_shown)

    # ---- 存取 ----
    def config(self) -> dict[str, Any]:
        """返回生效配置, 结构固定同 CONFIG_DEFAULTS (每叶必存在, 调用点可直接索引 cfg["worktree"]["enabled"])。
        磁盘可以是新嵌套/旧扁平/混合, 读取优先级: 嵌套新键 > 旧扁平键(deprecated) > 默认值。"""
        f = self.dir / "config.yaml"
        if not f.exists():
            raise SkeinError("未初始化 — 先跑 `skein.py init`")
        raw: dict[str, Any] = _yaml_load(f.read_text())
        # 缺键回填 (新增默认键时旧盘既无新嵌套键也无旧扁平键才补), 有变更才回写省磁盘; 已有旧扁平键的仓不被强制迁移
        filled = _cfg_backfill(raw)
        if filled != raw:
            f.write_text(_yaml_dump(filled))
            raw = filled
        cfg = _cfg_effective(raw)
        # 用户在插件启用时确认的 userConfig 优先于 config.yaml (经 CLAUDE_PLUGIN_OPTION_* 传入)
        for k in ("max_active",):
            v = os.environ.get(f"CLAUDE_PLUGIN_OPTION_{k.upper()}")
            if v and v.strip().isdigit():
                cfg[k] = int(v)
        return cfg

    def _hooks_cfg(self) -> dict[str, Any]:
        """读 config.yaml 原始 `hooks` 键 (不入 CONFIG_DEFAULTS, self.config() 不含; 见 c3b)。

        形状 = `hooks.<scope>.<when>`, scope 取 HOOK_SCOPES (9 个阶段名 + agent), 阶段名直接在
        hooks 下, **无中间 `stage` 层** —— 与 CONFIG_DEFAULTS 骨架逐字一致 (曾经读取端多套了一层
        `hooks.stage.<名>`, 于是照骨架填的配置静默不生效; 校验器接上后这类形状错会当场报出来)。

        缺失/非法语法 → {} 静默 (钩子是可选特性, 不该拖垮主命令)。结构错只 stderr 告警不阻断:
        本方法在钩子热路径上, 一个配置笔误不该让每条 skein 命令都退非零 (与 _yaml_bad 同策略)。
        硬报错交 `doctor` —— 那里是专门查配置的地方, 用户主动跑、看得见。
        """
        f = self.dir / "config.yaml"
        if not f.exists():
            return {}
        try:
            raw = _yaml_load(f.read_text())
        except ValueError:
            return {}  # 配置语法错误归 config()/doctor 报, 本处不重复阻断
        spec = raw.get("hooks")
        if not isinstance(spec, dict):
            return {}
        for e in hooks_schema_errors(spec):
            sys.stderr.write(f"⚠️  config.yaml {e}\n")
        return spec

    def _hook_ctx(self, tid: str, sid: str = "", t: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """阶段钩子 ctx: tid/sid/task_dir/worktree/repo_root, 供 hooks.runner._run_hooks 注入 env。"""
        worktree = ""
        if t:
            wts = worktrees_of(t)
            if wts:
                worktree = str(self.root / wts[0]["wt"])  # 单/首个 worktree; 多子git场景取首个
        return {"tid": tid, "sid": sid, "task_dir": str(self.tasks / tid) if tid else "",
                "worktree": worktree, "repo_root": str(self.root)}

    def _stage_hooks(self, stage: str, when: str, ctx: dict[str, Any]) -> None:
        """阶段 before/after 钩子入口 — create/confirm/start/check/finish/archive/subtask.* 共用。
        before 失败阻断该阶段 (SkeinError); after 失败仅告警, 阶段结果不变 (阻断语义见 hooks.runner._run_hooks)。
        无 hooks.<stage>.<when> 配置 → 零开销直返, 不构造 env/不 fork (design.md §5)。"""
        whens = self._hooks_cfg().get(stage)
        todo = whens.get(when) if isinstance(whens, dict) else None
        if not isinstance(todo, list) or not todo:
            return
        try:
            _run_hooks(stage, when, dict(ctx, hooks=todo))
        except HookBlocked as e:
            raise SkeinError(str(e))

    def _wt_shown(self) -> bool:
        # 禁用态 (worktree.enabled=false) 各出口不展示 worktree 段/列
        return bool(self.config()["worktree"]["enabled"])

    def config_cmd(self, a: argparse.Namespace) -> None:
        cfg = self.config()  # 生效值 (含 ENV override + 缺键回填), 结构固定同 CONFIG_DEFAULTS
        action = getattr(a, "action", None)
        if action is None:  # 无参 → 展示全部生效配置
            if getattr(a, "json", False):  # --json: 机器可解析嵌套结构 (skein config --json | jq -r .worktree.enabled)
                print(json.dumps(cfg, ensure_ascii=False))
                return
            for path in _cfg_paths():  # 扁平化点号展示, 如 spec.always_budget=8000
                print(f"{path}={_cfg_get_path(cfg, path)}")
            return
        if action == "reset":  # 全部重置为默认值 (覆写 config.yaml, 统一写回新嵌套格式)
            (self.dir / "config.yaml").write_text(_yaml_dump(dict(CONFIG_DEFAULTS)))
            print("已重置全部配置为默认值:")
            for path in _cfg_paths():
                print(f"{path}={_cfg_get_path(CONFIG_DEFAULTS, path)}")
                flat_key = next((fk for fk, (gk, lk) in _CFG_LEGACY.items() if f"{gk}.{lk}" == path), None)
                env_key = flat_key or path
                if os.environ.get(f"CLAUDE_PLUGIN_OPTION_{env_key.upper()}"):
                    print(f"注意: {path} 有 ENV override 生效, 实际读取仍为环境值 (写盘已重置)")
            return
        # set — 接受新点号路径 (如 worktree.enabled) 或旧扁平键 (如 use_worktree, deprecated 但仍生效)。
        # 写盘策略: 纯扁平旧仓 (盘上无同组嵌套叶) 原样写回扁平, 不代劳迁移; 但若盘上已有同组嵌套叶
        # (如 init 默认就写嵌套), 改写该嵌套叶而非另加扁平键 —— 否则嵌套读取优先级更高, 扁平 set 会被
        # 遮蔽变相失效 (见 _cfg_effective 优先级: 嵌套新键 > 旧扁平键)。
        key = a.key
        path = _CFG_LEGACY.get(key)
        path_str = f"{path[0]}.{path[1]}" if path else key
        if path_str not in _cfg_paths():
            raise SkeinError(f"未知配置键: {key} — 可用: {', '.join(_cfg_paths())}")
        try:
            val = _coerce_config(path_str, a.value)
        except (TypeError, ValueError):
            expect = type(_cfg_get_path(CONFIG_DEFAULTS, path_str)).__name__
            raise SkeinError(f"值类型不合: {key} 需 {expect}, 得 {a.value!r}")
        f = self.dir / "config.yaml"
        raw = _yaml_load(f.read_text()) if f.exists() else {}
        if key in _CFG_LEGACY and not (isinstance(raw.get(path[0]), dict) and path[1] in raw[path[0]]):
            # 旧扁平键 且 盘上尚无同名嵌套叶: 原样写回扁平 (纯扁平旧仓零破坏, 不代劳迁移)。
            raw[key] = val
        else:
            # 新点号路径, 或旧扁平键但盘上已有同组嵌套叶 (嵌套读取优先级更高, 不改嵌套则 set 会被遮蔽变相失效): 写嵌套结构。
            raw = _cfg_set_path(raw, path_str, val)
        f.write_text(_yaml_dump(raw))
        print(f"{key} = {val}")
        if os.environ.get(f"CLAUDE_PLUGIN_OPTION_{key.upper()}"):
            print(f"注意: {key} 有 ENV override 生效, 实际读取仍为环境值 (写盘已更新)")











    def _scaffold(self, tid: str, name: str) -> None:
        """落 planning 双工件脚手架 (prd 主入口 / design 详细设计).
        findings.md 不预建 — 仅真调研时由 skein-researcher 边研边增量生成 (无调研不产出)。
        模板极简 (只给骨架标题, 正文 planning 填), 避免占 token; 已存在则不覆盖。
        调度 DAG / 子任务不在此 — 归 task.json (脚本维护)。"""
        d = self.tasks / tid
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

    # ---- 命令 ----
    def fmt(self, a: argparse.Namespace) -> None:
        # 规范化 .skein/task/<id>/prd.md: 各章节内一级 `- ` list 项补 `- [ ]` todo (已勾选态保留),
        # 校验六标准章节齐备且顺序正确 (旧四段兼容 task 仅 warning), 不规范报错非零退出;
        # 仅内容变化才写 (天然幂等 + 防 hook 循环)。
        tid = a.id.strip()
        prd = self.tasks / tid / "prd.md"
        if not prd.exists():
            raise SkeinError(f"prd 不存在: {prd}")
        orig = prd.read_text()
        lines = orig.split("\n")
        # 校验: 至少一个一级标题 (# ...) + 六标准章节齐备且顺序正确 (旧四段兼容态只 warning)
        if not any(re.match(r"^#\s+\S", ln) for ln in lines):
            raise SkeinError(f"prd 不规范: 缺一级标题 (# ...) — {prd}")
        sections = [m.group(1).strip() for ln in lines
                    if (m := re.match(r"^##\s+(.+?)\s*$", ln))]
        if sections == PRD_SECTIONS_V4:
            print(f"prd 章节为旧四段 (兼容态, 建议迁六段模板: {PRD_SECTIONS_V6}) — {prd}", file=sys.stderr)
        elif sections != PRD_SECTIONS_V6:
            raise SkeinError(
                f"prd 不规范: 二级章节须为 {PRD_SECTIONS_V6} (齐备且顺序一致), "
                f"实际 {sections} — {prd}")
        # 规范化 (行首非缩进; 缩进子 list / 已勾选态不动):
        #   (a) 所有章节: `- ` 且非 checkbox → 补 `- [ ] `
        #   (b) 仅「目标」「验收标准」「Testing Decisions」章节: 有序列表 `N. ` → `- [ ] ` (逐条可勾选)
        #       User Stories 不在此列 —— 其 `1. As a ...` 编号格式是 to-spec 固定格式, 不折成 checkbox
        todo_sections = {"目标", "验收标准", "Testing Decisions"}
        out: list[str] = []
        changed, cur = 0, None
        for ln in lines:
            if h := re.match(r"^##\s+(.+?)\s*$", ln):
                cur = h.group(1).strip()
                out.append(ln)
                continue
            if m := re.match(r"^- (?!\[[ xX]\] )(.*)$", ln):
                out.append(f"- [ ] {m.group(1)}")
                changed += 1
            elif cur in todo_sections and (mo := re.match(r"^\d+\.\s+(.*)$", ln)):
                out.append(f"- [ ] {mo.group(1)}")
                changed += 1
            else:
                out.append(ln)
        new = "\n".join(out)
        if new == orig:
            print(f"prd 已规范, 无变化: {prd}")
            return
        prd.write_text(new)
        print(f"prd 已规范化: {prd} (补 {changed} 项 todo)")



    def init(self, _: argparse.Namespace) -> None:
        self.dir.mkdir(exist_ok=True)
        self.tasks.mkdir(exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        cfg = self.dir / "config.yaml"
        if not cfg.exists():
            cfg.write_text(_yaml_dump(dict(CONFIG_DEFAULTS)) + HOOKS_SKELETON)
        # .skein/.gitignore — 忽略自动渲染看板 (task.md 从 task.json 无损重建, 且 AI 禁读写)
        # + spec/.archive/ (完全重构可逆归档转储) + 衍生/临时 (hook 标记/审计日志/FTS 索引/软删转储)
        gi = self.dir / ".gitignore"
        GI_ENTRIES = [
            "task.md", "vision.md", "*.lock", "spec/.archive/",
            "spec/.pending-fix", "spec/.audit-log", "spec/.recall.db", "trash/",
        ]
        if not gi.exists():
            gi.write_text("# skein.py 自动渲染/衍生, 不入库\n" + "\n".join(GI_ENTRIES) + "\n")
        else:
            # 幂等补缺: 已存文件检查缺行补 (不破坏用户手写条目, 不重复已有)
            lines = gi.read_text(encoding="utf-8").splitlines()
            have = {ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")}
            missing = [e for e in GI_ENTRIES if e not in have]
            if missing:
                with gi.open("a", encoding="utf-8") as fh:
                    if lines and lines[-1].strip():
                        fh.write("\n")
                    fh.write("# skein 衍生/临时文件 (init 自动补缺)\n")
                    fh.write("\n".join(missing) + "\n")
        # worktree 目录在 git 根 (worktree.root), .skein/.gitignore 管不到 → 补到根 .gitignore
        # (仅 git 仓库需要; 非 git 无 worktree, 不制造多余 .gitignore)。子仓的忽略由 make_worktree 各自补。
        if self.git:
            ignore_worktree_dir(self.root, self.config())
        if not (self.dir / "task.json").exists():
            self.store.sync()
        self.store._write_board()
        print(f"已初始化 SKEIN 工作区: {self.dir}")

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
        if tid in self.store.used_ids():
            raise SkeinError(f"id 已占用: {tid} — 换一个 (含已归档的也不可复用)")
        # task 级父子层校验 (限 2 层: supertask→task→subtask)
        parent_id = (a.parent or "").strip() or None
        kind = a.kind or "task"
        if kind == "supertask" and parent_id:
            raise SkeinError(f"supertask 不可有 parent (supertask 是顶层父聚合层) — 去掉 --parent {parent_id}")
        if parent_id:
            p = self.store.load(parent_id)  # _load 不存在 → SkeinError「task 不存在」(parent 引用完整性)
            if p.get("parent"):
                # 被引用的 parent 自身是 child (其 parent != None) → 拒, 禁 child 作父, 深度超 2 层
                raise SkeinError(
                    f"深度超限: parent {parent_id} 本身是 child (其 parent={p.get('parent')!r}) — "
                    f"supertask 不可再嵌套 supertask (限 2 层: supertask→task→subtask)")
            if p.get("kind") == "supertask":
                parent_kind_ok = True
            elif p.get("kind") in (None, "task"):
                # 父是独立 task (kind=task 且 parent=None): 允许升格作 child 的聚合父 — 但更规范的做法是显式 supertask
                # ponytail: 不强制要求父必须 supertask, 只要 parent 链不超 2 层 (parent 的 parent=None 即可)
                parent_kind_ok = True
            else:
                raise SkeinError(f"parent {parent_id} kind={p.get('kind')!r} 非法 — 仅允许 task|supertask")
        repos = parse_repos(getattr(a, "repos", None))
        if repos and not self.config()["worktree"]["enabled"]:
            raise SkeinError(f"{tid} 声明 --repos 但 config worktree.enabled=false — 多子 git 隔离需启用 worktree")
        self._stage_hooks("create", "before", self._hook_ctx(tid))
        (self.tasks / tid).mkdir(parents=True)
        self._scaffold(tid, a.name)  # 落 prd/design/findings 脚手架 (planning 填)
        deps = [d.strip() for d in (a.deps or "").split(",") if d.strip()]
        t = {
            "id": tid, "name": a.name, "desc": a.desc,
            "status": S_PENDING, "deps": deps, "contracts": [], "subtasks": [],
            "priority": getattr(a, "priority", 5) or 5,  # 0-10, 默认 5 (中)
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
        self.store.save(t)  # _save 已渲染子任务看板
        self.store.sync()  # 刷新顶层 tasks 索引 + 看板 + html
        self._stage_hooks("create", "after", self._hook_ctx(tid, t=t))
        print(f"{tid}\t{self.tasks / tid}")






    def repos(self, a: argparse.Namespace) -> None:
        # 查/声明 task 的目标子 git (planning 声明: 每个各开 worktree)。仅 pending 可改 (start 后 worktree 已定)
        t = self.store.load(a.id)
        if a.set is None:
            print("\n".join(t.get("repos") or []) or "(未声明子 git — 单根/原地模式)")
            return
        if not self.config()["worktree"]["enabled"]:
            raise SkeinError(f"{a.id} config worktree.enabled=false — worktree 禁用, 不可声明 repos")
        if t["status"] not in (S_PENDING, S_READY):
            raise SkeinError(f"{a.id} 状态 {t['status']}, repos 只能在 start 前 (待处理/就绪) 声明")
        t["repos"] = parse_repos(a.set)
        self.store.save(t)
        self.store.sync()
        print(f"{a.id} repos = {', '.join(t['repos']) or '(空)'}")

    def estimate(self, a: argparse.Namespace) -> None:
        # 查/填 task 预计工时(小时)。plan 阶段必填, confirm 硬门校验 (见 _validate_estimate)。
        # 仅 pending/ready 可改 (start 后执行已启动, 工时估算不再变更调度)。
        t = self.store.load(a.id)
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
        self.store.save(t)
        self.store.sync()
        print(f"{a.id} estimate = {val} h")

    def deps(self, a: argparse.Namespace) -> None:
        # 查/补 task 级前置 DAG (dedup 排序用: 给散落 task 之间补执行序, 织成完整 DAG)。
        # 仅 pending 可改 (start 后调度已定); 且仅当现有 deps 为空才允许写 —
        # dedup 只对无依赖的 task 补新序, 既有依赖一律不碰 (防覆盖人工/plan 声明的前置)。
        t = self.store.load(a.id)
        if a.set is None:
            print(",".join(t.get("deps") or []) or "(无前置)")
            return
        if t["status"] not in (S_PENDING, S_READY):
            raise SkeinError(f"{a.id} 状态 {t['status']}, deps 只能在 start 前 (待处理/就绪) 设置")
        if t.get("deps"):
            raise SkeinError(
                f"{a.id} 已有前置 {','.join(t['deps'])} — 既有依赖不可改 (deps 只补无前置的 task)")
        new = [d.strip() for d in (a.set or "").split(",") if d.strip()]
        ids = self.store.used_ids()  # 含已归档, dep 指向归档 task 合法 (与 doctor 一致)
        for d in new:
            if d == a.id:
                raise SkeinError(f"{a.id} deps 自引用")
            if d not in ids:
                raise SkeinError(f"前置 task 不存在: {d}")
        # 环校验: 以拟设 deps 建全量未归档 task 级图, 检测环 (归档 task 不入图, 不成环)
        nodes = {x["id"] for x in self.store.all_tasks()}
        graph = {x["id"]: [d for d in x.get("deps", []) if d in nodes] for x in self.store.all_tasks()}
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
        self.store.save(t)
        self.store.sync()
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
        t = self.store.load(a.id)
        if t["status"] != S_PENDING:
            raise SkeinError(f"{a.id} 状态为 {t['status']}, 只能 confirm 待处理 (规划中) task")
        # planning 完成门: 无 subtask / prd 未填齐 / 预计工时未填 → 拒绝进就绪 (逼先补全规划)
        subs = t.get("subtasks") or []
        if len(subs) == 0:
            raise SkeinError(f"{a.id} 无 subtask 登记 — 先 skein subtask add 拆分再 confirm")
        validate_prd(self.tasks, a.id)
        validate_seam(self.tasks, a.id)
        self._validate_estimate(a.id, t)
        if getattr(a, "summary", False):
            # 只出摘要不改状态 — main 拿它塞进 AskUserQuestion。放在结构门之后: 结构不全时
            # 该先报缺什么, 而不是让用户去审一份残缺的 PRD。
            print(review_summary(self.tasks, a.id, t))
            return
        channel = self._require_user_review(a.id, bool(getattr(a, "approved", False)))
        self._stage_hooks("confirm", "before", self._hook_ctx(a.id, t=t))
        t["status"] = S_READY
        t["confirmed"] = now()
        t["confirmed_by"] = channel  # 审核渠道留痕: ask (AskUserQuestion) / user-tty (终端交互)
        self.store.save(t)
        self.store.sync()
        self._stage_hooks("confirm", "after", self._hook_ctx(a.id, t=t))
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

        抽成方法是为了给**自动启动**复用 —— `claim` / `subtask start` 认领到一个属于「就绪」
        task 的 subtask 时会调它 (见 `_ensure_task_active`), 那条路必须走**完全相同**的副作用:
        doctor 前置体检、task 级 max_active 校验、prd double-check、worktree 建立、started
        时间戳、start 的 before/after 阶段钩子。少任何一样, 自动启动的 task 就与手工 start 的
        不是同一种状态 —— 那类差异极难查 (表现是「有的 task 没 worktree」)。

        `quiet=True` 只压掉给人看的输出, 不跳过任何校验。
        """
        # start 前置体检: 跑 doctor 结构不变量检查, 有 ✗ 错误 → doctor 内 raise SkeinError 阻止 start
        if not quiet:
            print("start 前置体检 (doctor):")
        self.doctor(a)
        t = self.store.load(tid)
        if t["status"] != S_READY:
            raise SkeinError(
                f"{tid} 状态为 {t['status']}, 只能 start 就绪 task — "
                f"待处理(规划中) 须先 skein confirm 过用户确认门")
        cfg = self.config()
        active = self.store.active()
        if len(active) >= cfg["max_active"]:
            raise SkeinError(
                f"task 级并发上限 {cfg['max_active']} (当前 active: "
                f"{', '.join(x['id'] for x in active)}), 先 finish 一个再 start")
        undone = [d for d in t["deps"] if self._dep_unfinished(d)]
        if undone:
            raise SkeinError(f"前置未完成: {', '.join(undone)} — 先 finish 它们")
        # planning 完成门 (subtask + prd) 已在 confirm 时校验; 此处 double-check prd 防 confirm 后被改空
        validate_prd(self.tasks, tid)
        self._stage_hooks("start", "before", self._hook_ctx(tid, t=t))
        t["status"] = S_ACTIVE
        repos = t.get("repos") or []
        wt_cfg = cfg["worktree"]["enabled"]
        wt_on = self.git and wt_cfg  # 单根 worktree: 需根仓是 git; 配置禁用→原地执行
        # --repos 的 git 性由 _mkwt 逐子仓校验 (worktree 落各子仓内), 与父目录是否 git 无关 —
        # 故只在 config 显式禁用时挡, 不吃 self.git (支持非 git 父 + 多 git 子的微服务布局)。
        if repos and not wt_cfg:
            raise SkeinError(
                f"{tid} 声明了 --repos 但 config worktree.enabled=false — 多子 git 隔离需启用 worktree")
        if repos:
            # 多子 git: planning 声明的每个子 git 各开 worktree+branch (并列 repo / submodule 同理)
            t["worktrees"] = [make_worktree(t, r, cfg, self.root) for r in repos]
            t["worktree"] = ", ".join(w["wt"] for w in t["worktrees"])  # 显示汇总
        elif wt_on:
            rel = f"{cfg['worktree']['root']}/skein-{tid}"  # 相对 project root 存盘, 免机器绝对路径入库
            git("worktree", "add", "-b", t["branch"], str(self.root / rel), "HEAD", cwd=self.root)
            t["worktree"] = rel
            t["worktrees"] = [{"repo": ".", "wt": rel, "branch": t["branch"], "merged": False}]
        else:
            t["worktree"] = None  # 非 git / config 禁用, 无 repos: 原地执行, 无 worktree 隔离
            t["worktrees"] = []
        if not t.get("started"):
            t["started"] = now()  # exec 时刻 (首次 start; 重启不覆盖)
        self.store.save(t)
        self.store.sync()
        if t["worktrees"]:
            loc = "\n".join(f"worktree: {w['wt']} (子 git: {w['repo']}, branch: {w['branch']})"
                            for w in t["worktrees"])
        else:
            reason = "config worktree.enabled=false" if self.git else "非 git 仓库"
            loc = f"{reason}: 原地执行 (无 worktree 隔离)"
        self._stage_hooks("start", "after", self._hook_ctx(tid, t=t))
        if not quiet:
            print(f"{tid} started\n{loc}")
        return t

    def check(self, a: argparse.Namespace) -> None:
        # 进行中→检查中: 记 checked 时刻 (board 展示等待/执行时间用)。仅 active 可进检查。
        t = self.store.load(a.id)
        if t["status"] != S_ACTIVE:
            raise SkeinError(f"{a.id} 状态 {t['status']}, 只有进行中 task 能进检查")
        self._stage_hooks("check", "before", self._hook_ctx(a.id, t=t))
        t["status"] = S_CHECK
        t["checked"] = now()
        self.store.save(t)
        self.store.sync()
        self._stage_hooks("check", "after", self._hook_ctx(a.id, t=t))
        print(f"{a.id} checked")

    def _dep_unfinished(self, dep: str) -> bool:
        # 归档即视为完成
        if self.store.archived_path(dep):
            return False
        f = self.tasks / dep / "task.json"
        if not f.exists():
            return False  # 未知 dep 不阻塞
        return cast(str, json.loads(f.read_text())["status"]) != S_DONE

    def finish(self, a: argparse.Namespace) -> None:
        tid = a.id
        t = self.store.load(tid)
        if t["status"] not in STATUS_INFLIGHT:
            raise SkeinError(f"{tid} 状态 {t['status']}, 非在途 (进行中/检查中) 无法 finish")
        # supertask 聚合归档: finish 前所有 child task(parent 指向它)须全 done
        # ponytail: 遍历 tasks 过滤 parent==tid 找 child (不维护 child_ids 数组, 真值源单一)
        if t.get("kind") == "supertask":
            pending = [c["id"] for c in self.store.all_tasks() if c.get("parent") == tid and c["status"] != S_DONE]
            if pending:
                raise SkeinError(
                    f"{tid} 是 supertask, 仍有未完成 child task: {', '.join(pending)} — "
                    f"先 finish 全部 child 再 finish super (聚合归档要求 child 全 done)")
        cfg = self.config()
        wts = worktrees_of(t)
        self._stage_hooks("finish", "before", self._hook_ctx(tid, t=t))
        conflicts: list[tuple[str, str]] = []  # [(repo, 冲突输出)] — 部分子 git 冲突时保留已合并进度, task 留 active 供幂等重跑
        for w in wts:
            if w.get("merged"):
                continue  # 幂等: 前次已合并的子 git 跳过 (部分冲突重跑场景)
            sub = self.root if w["repo"] == "." else self.root / w["repo"]  # merge 落各子 git
            wt = self.root / w["wt"]
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
            self.store.save(t)
            self.store.sync()
            detail = "\n".join(f"  子 git {r}: 冲突已 abort" for r, _ in conflicts)
            raise SkeinError(
                f"{tid} 部分子 git 合并冲突, 已合并的保留、task 仍 active。"
                f"解冲突后重跑 finish (幂等跳过已合并):\n{detail}")
        t["status"] = S_DONE
        t["worktree"] = None
        t["worktrees"] = []
        t["finished"] = now()  # 完成时刻 — 保留期从此计, 超 retain_days 由 _autoclean 归档
        self.store.save(t)
        self.store.sync()  # 重写顶层索引 (完成 task 仍留看板; retain_days=0 时 _autoclean 即归档)
        archived = not (self.tasks / tid).exists()  # retain_days<=0 → 已被 _autoclean 归档
        # 原地模式 (无 worktree): 此时才轮到 auto_commit 决定提不提交; 关则改动留工作区由用户自管。
        # 放在 _save/_sync 之后 — 连同 .skein 状态一起提交, 免留下脏索引
        if not wts and self.git and cfg.get("auto_commit", True):
            commit_all(self.root, f"skein({tid}): {t['name']}")
        cfg = self.config()
        rest = self.store.active()
        tail = (f", 剩余 active: {', '.join(x['id'] for x in rest)}" if rest else ", 无剩余 active")
        keep = "已归档" if archived else f"保留 {cfg.get('retain_days', 7)} 天后自动归档"
        self._stage_hooks("finish", "after", self._hook_ctx(tid, t=t))
        print(f"{tid} finished ({keep})" + tail)

    def archive(self, a: argparse.Namespace) -> None:
        # 归档 = 丢弃 (不 merge): 先销 worktree/branch, 免残留悬挂
        f = self.tasks / a.id / "task.json"
        t = json.loads(f.read_text()) if f.exists() else None
        self._stage_hooks("archive", "before", self._hook_ctx(a.id, t=t))
        if t is not None:
            for w in worktrees_of(t):
                sub = self.root if w["repo"] == "." else self.root / w["repo"]
                wt = self.root / w["wt"]
                if wt.exists():
                    git("worktree", "remove", str(wt), "--force", cwd=sub, check=False)
                git("branch", "-D", w["branch"], cwd=sub, check=False)
        self.store.archive_task(a.id)
        self.store.sync()  # 重写顶层 tasks 索引 (去掉已归档 task)
        self._stage_hooks("archive", "after", self._hook_ctx(a.id, t=t))
        print(f"{a.id} archived")


    def del_(self, a: argparse.Namespace) -> None:
        # 删 task (软删 → .skein/trash/<id>.<date>/, 可恢复) 或单 subtask (直接移除, 不进 trash)
        tid = a.task_id
        src = self.tasks / tid
        if not src.exists() or not (src / "task.json").exists():
            raise SkeinError(f"task 不存在: {tid}")
        t = self.store.load(tid)

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
            self.store.save(t)  # _save 渲染子任务看板
            self.store.sync()   # 刷顶层索引 + 看板
            print(f"{tid}/{sid} removed ({len(new_subs)} subtask 剩余)")
            return

        if a.dry_run:
            lines = [f"[dry-run] 将删 task {tid} ({t['name']}):",
                     f"  软删: {src} → {self.trash_dir}/{tid}.{datetime.datetime.now().strftime('%Y%m%d')}/"]
            if t["status"] in STATUS_INFLIGHT:
                for w in worktrees_of(t):
                    lines.append(f"  销 worktree: {w['wt']}  分支: {w['branch']}  (子 git {w['repo']})")
            print("\n".join(lines))
            return

        # 在途 task (进行中/检查中) 先销 worktree/分支 (finish/archive 同策略, 免悬挂); 待处理/就绪/done 无 worktree, 跳过
        if t["status"] in STATUS_INFLIGHT:
            destroy_worktrees(t, self.root)
        dst = self.trash_dir / f"{tid}.{datetime.datetime.now().strftime('%Y%m%d')}"
        self.trash_dir.mkdir(parents=True, exist_ok=True)
        if dst.exists():  # 同日重复删同 id → 先清旧 (同名目录 shutil.move 跨平台行为不一)
            shutil.rmtree(dst)
        shutil.move(str(src), str(dst))
        self.store.sync()  # 刷顶层索引 (移除该 task) + 看板
        print(f"{tid} deleted (软删可恢复: {dst})")

    def rename(self, a: argparse.Namespace) -> None:
        # 重命名 task/subtask 的 id 或 name (至少给一个 --id / --name)。
        # - 无 sid: 改 task。--name 改显示名 (任意状态); --id 改 id (仅 pending, 同步目录/branch/别 task deps/child parent/顶层索引)
        # - 带 sid: 改 subtask。--name 改子任务名; --id 改 sid (同步同 task 内别 subtask 的 depends_on 引用)
        tid = a.tid
        t = self.store.load(tid)  # 不存在即 SkeinError
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
            self.store.save(t)
            self.store.sync()
            print(f"{tid}/{a.sid} renamed"
                  + (f" → sid={new_id}" if new_id else "")
                  + (f" name={new_name!r}" if new_name is not None else ""))
            return

        # 改 task
        if new_name is not None:
            t["name"] = new_name
        if not new_id:  # 仅改 name
            self.store.save(t)
            self.store.sync()
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
        if new_id in self.store.used_ids():
            raise SkeinError(f"id 已占用: {new_id} — 换一个 (含已归档的也不可复用)")
        old_id = t["id"]
        t["id"] = new_id
        t["branch"] = f"skein/{new_id}"  # pending 无 worktree, 只更 branch 字符串
        # 目录改名 (旧 → 新), 再经 _save 按新 id 落 task.json + 刷子任务看板
        # ponytail: prd.md 脚手架内的 `subtask list <old-id>` 提示行不重写 (planning 后 prd 已被 AI 大改, 属 AI 内容, 非脚本真值)
        shutil.move(str(self.tasks / old_id), str(self.tasks / new_id))
        self.store.save(t)
        for other in self.store.all_tasks():  # 同步别 task 的 deps + child 的 parent 引用
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
                self.store.save(other)
        self.store.sync()
        print(f"{old_id} renamed → {new_id}")


    def clean(self, a: argparse.Namespace) -> None:
        # 用户主动清理 (skein-clean skill 唯一入口): 归档完成超 --days 天的 task。
        # ponytail: --days 只能比 config retain_days 更激进 (更小); 更大值被 _sync 的自动 ceiling 归档抵消。
        archived = self.store.autoclean(days=a.days)
        self.store.sync()
        d = a.days if a.days is not None else self.config().get("retain_days", 7)
        if archived:
            print(f"已归档 {len(archived)} 个完成 task (超 {d} 天保留期): {', '.join(archived)}")
        else:
            print(f"无超 {d} 天保留期的完成 task 可归档")
        rest = self.store.all_tasks()
        blocked = self._unfinished_related(rest)
        held = sorted(t["id"] for t in rest if t["id"] in blocked and t["status"] == S_DONE)
        if held:
            print(f"跳过 {len(held)} 个完成 task (关联链上仍有未完成): {', '.join(held)}")

    def current(self, a: argparse.Namespace) -> None:
        active = self.store.active()
        if not active:
            print("无 active task")
            return
        wt_col = self._wt_shown()
        for t in active:
            if wt_col:
                print(f"{t['id']}\t{t['status']}\t{t['name']}\t{t.get('worktree') or '-'}")
            else:
                print(f"{t['id']}\t{t['status']}\t{t['name']}")

    def ready(self, a: argparse.Namespace) -> None:
        # task 级可启动批 (脚本算, 非 AI 判): 就绪态 (已过 confirm 门) + 前置全 done + 有空闲 active 槽位。
        # 与 subtask ready 同构, 但只读预览 (start 才占槽); task 无写集字段, 故不算写集冲突。
        slots = self.config()["max_active"] - len(self.store.active())
        if slots <= 0:
            print(f"无空闲 active 槽 (上限 {self.config()['max_active']} 已满) — 先 finish 一个再 start")
            return
        picked: list[dict[str, Any]] = []
        for t in self.store.all_tasks():
            if t["status"] != S_READY:
                continue
            undone = [d for d in t["deps"] if self._dep_unfinished(d)]
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
        t = self.store.load(a.tid)
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
        if self._wt_shown():
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
            self._dep_unfinished(d) for d in t.get("deps", []))
        wt_shown = self._wt_shown()
        return {"id": t["id"], "status": t["status"], "name": t.get("name", ""),
                "desc": t.get("desc", ""), "deps": t.get("deps", []),
                "repos": t.get("repos", []),
                "worktree": (t.get("worktree") or None) if wt_shown else None,
                "worktrees": [{"repo": w["repo"], "wt": w["wt"]} for w in worktrees_of(t)] if wt_shown else [],
                "pct": pct, "subs": cnt, "ready": ready}

    def list_(self, a: argparse.Namespace) -> None:
        tasks = self.store.all_tasks()
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

    def contract(self, a: argparse.Namespace) -> None:
        t = self.store.load(a.id)
        t.setdefault("contracts", [])
        if a.add:
            t["contracts"].append(a.add)
            self.store.save(t)
            print(f"{a.id} 契约 +1 (共 {len(t['contracts'])})")
        elif not t["contracts"]:
            print("无契约")
        else:
            for i, c in enumerate(t["contracts"], 1):
                print(f"{i}. {c}")








    def prd(self, a: argparse.Namespace) -> None:
        """prd 章节 CLI 入口: read/write/add/check/uncheck <id> --type <章节> [--list TEXT]。
        task 必须存在 (经 _load 守); --type 经 PRD_TYPE_ALIAS 归一到中文章节名。"""
        tid = a.id.strip()
        self.store.load(tid)  # task 存在性校验 (不存在 raise SkeinError)
        raw_type = a.type
        if raw_type not in PRD_TYPE_ALIAS:
            raise SkeinError(f"非法 --type: {raw_type!r} — 合法值: {list(PRD_TYPE_ALIAS.keys())}")
        section = PRD_TYPE_ALIAS[raw_type]
        act = a.action
        if act == "read":
            body = section_read(self.tasks, tid, section)
            print(body)
            return
        if not a.list:
            raise SkeinError(f"{act} 需要 --list (文本内容, \\n 多行)")
        if act == "add":
            section_add(self.tasks, tid, section, a.list)
            print(f"{tid}「{section}」章节 +{len(a.list.split(chr(10)))} 条 (追加, 已有保留)")
        elif act == "write":
            section_write(self.tasks, tid, section, a.list)
            print(f"{tid}「{section}」章节整章重建")
        elif act == "check":
            n = section_check(self.tasks, tid, section, a.list, flag=True)
            print(f"{tid}「{section}」勾选 {n} 条 (匹配「{a.list}」)")
        elif act == "uncheck":
            n = section_check(self.tasks, tid, section, a.list, flag=False)
            print(f"{tid}「{section}」反勾选 {n} 条 (匹配「{a.list}」)")
        else:
            raise SkeinError(f"未知 prd 动作: {act}")







    def board(self, a: argparse.Namespace) -> None:
        self.store._write_board()
        print(f"看板已更新: {self.dir / 'task.md'}")



    # ---- subtask DAG 调度 (单 task 内, 存 per-task task.json 的 subtasks[]) ----
    def _ready(self, t: dict[str, Any]) -> list[dict[str, Any]]:
        """就绪批: pending + 依赖全 done, 按统筹学关键路径权重降序排序后截到空闲槽位
        (关键路径优先 = 最长下游链先派, 最小化 makespan; 并行只看 depends_on DAG, 无写文件冲突自算)。"""
        subs = t.get("subtasks", [])
        done = {s["sid"] for s in subs if s["status"] == SS_DONE}
        running = [s for s in subs if s["status"] == SS_RUNNING]
        slots = self.config()["max_active"] - len(running)
        if slots <= 0:
            return []  # 并发满 → 阻塞
        crit = _crit_weight(subs)
        cand = [(i, s) for i, s in enumerate(subs)
                if s["status"] == SS_PENDING
                and all(d in done for d in s.get("depends_on", []))]
        # 关键路径优先: 权重降序, 同权重按登记序稳定 (i 升序)
        cand.sort(key=lambda p: (-crit.get(p[1]["sid"], 0), p[0]))
        return [s for _, s in cand[:slots]]

    def _schedulable(self) -> list[dict[str, Any]]:
        """可被调度的 task: **进行中 + 就绪(前置已清)**, 按登记序。

        「就绪」也算可调度是刻意的 —— 就绪 = 已过人审门、规划完成、只差开工。要求先手工
        `skein start` 再派 subtask, 等于在已经确认过的东西上再要一次仪式, 而那一步没有任何
        新信息进来。改为**首个 subtask 被认领时自动启动**该 task (见 `_ensure_task_active`)。

        前置未完成的就绪 task 不进池 —— 与 `start` 的 deps 门同一判据, 免得自动启动绕过它。
        """
        active = self.store.active()
        active_ids = {t["id"] for t in active}
        ready = [t for t in self.store.all_tasks()
                 if t["status"] == S_READY and t["id"] not in active_ids
                 and not any(self._dep_unfinished(d) for d in t.get("deps", []))]
        return active + ready

    def _ensure_task_active(self, t: dict[str, Any], a: argparse.Namespace) -> dict[str, Any]:
        """若 task 还在「就绪」, 就地把它启动 (进行中 + worktree)。已是进行中则原样返回。

        走的是与手工 `skein start` **完全相同**的 `_start_task`, 所以 doctor 体检、task 级
        max_active、prd double-check、worktree、started 时间戳、start 阶段钩子一个不少。
        task 级并发满时 `_start_task` 会抛 —— 自动启动**不得**绕过那道上限, 抛出来是对的。
        """
        if t["status"] != S_READY:
            return t
        return self._start_task(t["id"], a, quiet=True)

    def _global_ready(self) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        """全局跨 task 就绪批: 所有**可调度** task (进行中 + 就绪) 的 ready subtask 合池,
        按 (拓扑深度降序, task 登记序, subtask 登记序) 排序, 截到全局 max_active - 全局 running 槽。
        返回 [(task_obj, subtask_obj), ...]。"""
        tasks = self._schedulable()
        global_running = sum(
            1 for t in tasks for s in t.get("subtasks", []) if s["status"] == SS_RUNNING)
        slots = self.config()["max_active"] - global_running
        if slots <= 0:
            return []
        cand: list[tuple[dict[str, Any], dict[str, Any], int, int, int]] = []
        for ti, t in enumerate(tasks):
            subs = t.get("subtasks", [])
            done = {s["sid"] for s in subs if s["status"] == SS_DONE}
            crit = _crit_weight(subs)
            for i, s in enumerate(subs):
                if s["status"] != SS_PENDING:
                    continue
                if not all(d in done for d in s.get("depends_on", [])):
                    continue  # 依赖未全 done 不入池
                cand.append((t, s, ti, i, crit.get(s["sid"], 0)))
        # 拓扑深度降序 → task 登记序 → subtask 登记序 (active task 同级, 不再分 task 优先级)
        cand.sort(key=lambda x: (-x[4], x[2], x[3]))
        return [(c[0], c[1]) for c in cand[:slots]]

    def _sub(self, t: dict[str, Any], sid: str) -> dict[str, Any]:
        for s in t.get("subtasks", []):
            if s["sid"] == sid:
                return cast(dict[str, Any], s)
        raise SkeinError(f"subtask 不存在: {t['id']}/{sid}")

    def claim(self, a: argparse.Namespace) -> None:
        """全局跨 task 认领就绪批: 所有 active task ready subtask 竞争全局 max_active 槽。
        整批标 running + 各 task 各 _save。无 tid (对照 `subtask claim <tid>` 单 task)。
        `--dry-run`: 只读预览整批 (与默认认领同源排序), 不改状态 (旧 pop)。"""
        batch = self._global_ready()
        if getattr(a, "dry_run", False):
            if not batch:
                tasks = self.store.active()
                grun = sum(1 for t in tasks for s in t.get("subtasks", []) if s["status"] == SS_RUNNING)
                gpend = sum(1 for t in tasks for s in t.get("subtasks", []) if s["status"] == SS_PENDING)
                mp = self.config()["max_active"]
                print(f"无全局就绪 subtask (全局 running: {grun}/{mp}, pending: {gpend}) — 满槽或依赖未完成")
                if mp - len(tasks) > 0:
                    for t in self.store.all_tasks():
                        if t["status"] != S_READY or any(self._dep_unfinished(d) for d in t["deps"]):
                            continue
                        print(f"有就绪 task 待启动: {t['id']} ({t['name']})")
                        print(f"— 直接启动执行: `skein.py start {t['id']}` (待处理 task 须先 skein confirm 过确认门)")
                        break
                return
            print("全局就绪批 (只读预览, 不改状态) — 决定执行后去掉 --dry-run 认领:")
            for t, s in batch:
                sk = ",".join(s.get("skills", [])) or "-"
                chk = "; ".join(s.get("验收", [])) or "-"
                print(f"{t['id']}/{s['sid']}\t{s['name']}\tskills: {sk}\t验收: {chk}")
            print("— 认领整批: `skein.py claim`  或只占单个: `skein.py subtask start <tid> <sid>`")
            return
        if not batch:
            tasks = self._schedulable()
            grun = sum(1 for t in tasks for s in t.get("subtasks", []) if s["status"] == SS_RUNNING)
            gpend = sum(1 for t in tasks for s in t.get("subtasks", []) if s["status"] == SS_PENDING)
            mp = self.config()["max_active"]
            print(f"无全局就绪 subtask (全局 running: {grun}/{mp}, pending: {gpend}) — 满槽或依赖未完成")
            return
        # 按 task 分组认领: 属于「就绪」task 的, 先把该 task 就地启动 (进行中 + worktree),
        # 再标 subtask running。启动会重写 task.json, 所以必须拿**启动后**的对象再找 subtask,
        # 否则改的是一份马上被覆盖掉的旧副本 (改了等于没改, 且不报错)。
        by_tid: dict[str, list[str]] = {}
        order: list[str] = []
        for t, s in batch:
            if t["id"] not in by_tid:
                by_tid[t["id"]] = []
                order.append(t["id"])
            by_tid[t["id"]].append(s["sid"])
        claimed: list[tuple[str, dict[str, Any]]] = []
        started_now: list[str] = []
        for tid in order:
            t = next(x for x, _ in batch if x["id"] == tid)
            if t["status"] == S_READY:
                t = self._ensure_task_active(t, a)   # 满槽会抛 — 自动启动不绕并发上限
                started_now.append(tid)
            subs = {s["sid"]: s for s in t.get("subtasks", [])}
            for sid in by_tid[tid]:
                s = subs[sid]
                s["status"] = SS_RUNNING
                if not s.get("started"):
                    s["started"] = now()  # exec 时刻 (首次认领, 重认领不覆盖)
                claimed.append((tid, s))
            self.store.save(t)
        if started_now:
            print(f"自动启动就绪 task (首个 subtask 被认领): {', '.join(started_now)}")
        print("已全局认领 (running) — main 逐个派 skein-executor（dispatch 只给 tid + sid + 工作目录）, 完成即 subtask done/fail:")
        for tid, s in claimed:
            sk = ",".join(s.get("skills", [])) or "-"
            chk = "; ".join(s.get("验收", [])) or "-"
            print(f"{tid}/{s['sid']}\t{s['name']}\tskills: {sk}\t验收: {chk}")

    def subtask(self, a: argparse.Namespace) -> None:
        if a.action == "add":
            t = self.store.load(a.tid)
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
                "验收": _split_semi(a.check),  # 验收标准 checklist (字符串数组)
                "验收done": [],  # 已通过验收标准序号(1-based); 完成百分比 = len/len(验收)
                "status": SS_PENDING,
                "skills": _split(a.skills),  # 关联 skills (0-n)
                "created": now(),   # 创建时刻
                "started": None,    # exec 时刻 (claim/start →运行中 时置)
                "finished": None,   # 完成时刻 (done 时置)
            })
            self.store.save(t)  # _save 已渲染子任务看板
            print(f"{a.tid}/{a.sid} 已登记 ({est} h; 共 {len(subs)} subtask, "
                  f"合计 {_sub_estimate_sum(t)} h)")
            return
        if a.action == "list":
            t = self.store.load(a.tid)
            subs = t.get("subtasks", [])
            if not subs:
                print("无 subtask")
                return
            for s in subs:
                deps = ",".join(s.get("depends_on", [])) or "-"
                chk = "; ".join(s.get("验收", [])) or "-"
                sk = ",".join(s.get("skills", [])) or "-"
                est = s.get("estimate")
                print(f"{s['sid']}\t{s['status']}\t{_sub_pct(s)}%\t{est if est else '-'}h\t{s['name']}"
                      f"\t依赖:{deps}\t验收:{chk}\tskills:{sk}")
            return
        if a.action == "show":
            t = self.store.load(a.tid)
            s = self._sub(t, a.sid)
            crit = s.get("验收", [])
            doneidx = set(s.get("验收done", []))
            est = s.get("estimate")
            elapsed = None
            if s.get("started") and s.get("finished"):
                elapsed = round((s["finished"] - s["started"]) / 60, 1)  # 分钟
            print(f"sid: {s['sid']}")
            print(f"name: {s['name']}")
            print(f"desc: {s.get('desc') or '-'}")
            print(f"status: {s['status']}")
            print(f"estimate: {est if est else '-'} h")
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
            t = self.store.load(a.tid)
            batch = self._ready(t)
            if not batch:
                run = [s["sid"] for s in t.get("subtasks", []) if s["status"] == SS_RUNNING]
                pend = [s for s in t.get("subtasks", []) if s["status"] == SS_PENDING]
                print(f"无就绪 subtask (running: {','.join(run) or '-'}, "
                      f"pending: {len(pend)}) — 满槽或依赖未完成")
                return
            if a.action == "claim":
                # 一次性认领: 就绪批整体标 running, 免 main 逐个 start (少一轮往返 + 无竞态窗口)
                for s in batch:
                    s["status"] = SS_RUNNING
                    if not s.get("started"):
                        s["started"] = now()  # exec 时刻 (首次认领, 重认领不覆盖)
                self.store.save(t)  # _save 已渲染子任务看板
                print("已认领 (running) — main 逐个派 skein-executor（dispatch 只给 tid + sid + 工作目录）, 完成即 subtask done/fail:")
            else:
                print("就绪 (只读预览, 认领用 `subtask claim`):")
            for s in batch:
                sk = ",".join(s.get("skills", [])) or "-"
                chk = "; ".join(s.get("验收", [])) or "-"
                print(f"{s['sid']}\t{s['name']}\tskills: {sk}\t验收: {chk}")
            return
        # start / done / fail 均针对单 sid
        t = self.store.load(a.tid)
        s = self._sub(t, a.sid)
        if a.action == "start":
            if s["status"] not in (SS_PENDING, SS_FAILED):
                raise SkeinError(f"{a.sid} 状态 {s['status']}, 只能 start 待处理/失败")
            done = {x["sid"] for x in t["subtasks"] if x["status"] == SS_DONE}
            undone = [d for d in s.get("depends_on", []) if d not in done]
            if undone:
                raise SkeinError(f"依赖未完成: {', '.join(undone)} — 先 done 它们")
            run = [x for x in t["subtasks"] if x["status"] == SS_RUNNING]
            if len(run) >= self.config()["max_active"]:
                raise SkeinError(f"并发已满 ({len(run)}) — 先 done 一个再 start")
            # task 还在「就绪」→ 就地启动 (与 claim 同一条路, 见 _ensure_task_active)。
            # 启动会重写 task.json, 所以要拿启动后的对象重新定位 subtask, 否则改的是旧副本。
            if t["status"] == S_READY:
                t = self._ensure_task_active(t, a)
                s = self._sub(t, a.sid)
                print(f"自动启动就绪 task: {a.tid}")
            self._stage_hooks("subtask.start", "before", self._hook_ctx(a.tid, a.sid, t=t))
            s["status"] = SS_RUNNING
            if not s.get("started"):
                s["started"] = now()  # exec 时刻 (首次 start, 重启不覆盖)
        elif a.action == "check":
            crit = s.get("验收", [])
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
            s["验收done"] = idx
            self.store.save(t)  # _save 已渲染子任务看板
            print(f"{a.tid}/{a.sid} 验收 {len(idx)}/{len(crit)} ({_sub_pct(s)}%)")
            return
        elif a.action == "done":
            self._stage_hooks("subtask.done", "before", self._hook_ctx(a.tid, a.sid, t=t))
            s["status"] = SS_DONE
            s["finished"] = now()  # 完成时刻
            s["验收done"] = list(range(1, len(s.get("验收", [])) + 1))  # 完成即全过 → 100%
        elif a.action == "fail":
            self._stage_hooks("subtask.fail", "before", self._hook_ctx(a.tid, a.sid, t=t))
            s["status"] = SS_FAILED
            s["finished"] = now()  # 失败时刻 (与 done 对称)
            if a.note:
                s["note"] = a.note  # 失败备注 (运行时, 非 planning schema)
        self.store.save(t)  # _save 已渲染子任务看板
        if a.action in ("start", "done", "fail"):
            self._stage_hooks(f"subtask.{a.action}", "after", self._hook_ctx(a.tid, a.sid, t=t))
        print(f"{a.tid}/{a.sid} → {s['status']}")













    _LOCK_ID_PATH = "/__skein__/id"  # 身份探测端点: 返回本服务的项目标识 (.skein 绝对路径)
    _REV_PATH = "/__skein__/rev"  # 版本探测端点: rev 变则 reload (WS 推送为主, 轮询兜底)
    _LIVE_PATH = "/__skein__/live"  # 热重载 WebSocket: rev 变时 server 推 "reload", 浏览器即刷


















    def setup(self, a: argparse.Namespace) -> None:
        # 默认兼容: 拷 spec/task 入 .skein + 删 trellis 接线 (避免双注入), 留 .trellis 数据。
        # --full: 兼容全套 + 整删 .trellis/ (spec/task 已拷走)。
        trellis = self.root / ".trellis"
        # scaffold 确认走 stderr, 保 stdout 纯 JSON manifest (agent/脚本单一解析口)
        with contextlib.redirect_stdout(sys.stderr):
            self.init(a)  # 幂等 scaffold: .skein/ + config + gitignore + 顶层看板
        tspec = trellis / "spec"
        sspec = self.dir / "spec"
        spec_copied = False
        if tspec.is_dir() and not sspec.exists():
            shutil.copytree(tspec, sspec)  # 独立拷贝: trellis 零改动, spec 归 skein 自管 (软链会锁死双向)
            spec_copied = True
        elif not tspec.exists() and not sspec.exists():
            # 无 trellis → 建本地 spec 库 (spec.py init)
            subprocess.run([sys.executable, str(SPEC_ENTRY), "init"],
                           stdout=sys.stderr, check=False)
        # 物理迁移 trellis task 文件夹 (redirect 内, 保 stdout 纯 JSON)
        with contextlib.redirect_stdout(sys.stderr):
            tasks = migrate_trellis_tasks(trellis, self.tasks, self.store)
        # 无条件删接线 (两模式), --full 再整删 .trellis 目录
        removed = purge_wiring(trellis, self.root)
        removed += purge_trellis_hooks(self.root)  # 剔 settings*.json 内 canonical trellis hook 条目 + 删脚本
        trellisx_disabled = disable_trellisx_plugin(self.root)  # settings.local.json 禁 trellisx 插件 (防双注入)
        trellis_removed = False
        if a.full and trellis.is_dir():
            shutil.rmtree(trellis); removed.append(".trellis/"); trellis_removed = True
        # web 看板服务: 缺省启用 (init 已写 web.serve=true); --no-web 关闭。启用则打开看板一次 (监听服务由 monitor 起)。
        web_enabled = not getattr(a, "no_web", False)
        if not web_enabled:
            cfgf = self.dir / "config.yaml"
            cfg = _yaml_load(cfgf.read_text())
            cfg = _cfg_set_path(cfg, "web.serve", False)
            cfgf.write_text(_yaml_dump(cfg))
        else:
            print("可视化看板: 运行 `skein view` 起 http 服务打开 (常驻服务由 monitor 起)。", file=sys.stderr)
        manifest = {
            "web_serve": web_enabled,
            "mode": "full" if a.full else "compat",
            "trellis_present": trellis.exists(),
            "spec_copied": spec_copied,
            "spec_needs_reorg": spec_copied,  # 拷自 trellis → agent 重组为 namespace×类目 (在 .skein/spec 原地改, 安全)
            "trellis_tasks": tasks,  # 已物理迁入 .skein/task/; agent 只补语义 (subtask/contract)
            "wiring_removed": removed,  # 已删的 trellis 接线 + (full 时) .trellis/
            "trellisx_disabled": trellisx_disabled,  # 已在 .claude/settings.local.json 禁用的 trellisx 插件 key
            "trellis_removed": trellis_removed,
            "settings_need_manual_edit": settings_trellis_notes(self.root),
        }
        print(json.dumps(manifest, ensure_ascii=False, indent=2))


# ==== 看板视图层 (纯投影): Snapshot 单一输入 + 无 self 的 _view_* 函数族 ====
# 一次目录扫描 → Snapshot; 6 个 board 视图皆纯函数 view(snapshot)→dict, 喂假 Snapshot 即可断言。
# 调度/mutation 仍走 Skein 上的严格 _all()/_dep_unfinished (幽灵骨架不可派发); 此层只读只投影。
