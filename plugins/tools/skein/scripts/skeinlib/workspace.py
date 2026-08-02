"""`Workspace` — 一个 `.skein/` 工作区的**共享底座**: 路径、生效配置、落盘层、阶段钩子。

## 为什么单独一层
`Lifecycle` / `Scheduler` / `Query` / `Artifacts` / `Admin` 五个协作对象都要读同一批东西:
仓库根在哪、配置怎么算、task.json 谁写、钩子怎么触发。把它们做成构造入参而不是散落的 `self.X`,
**构造签名就是依赖清单** —— 想知道 `Scheduler` 碰什么, 看它的 `__init__` 就够了。

## 谁持有它
`Skein` (commands.py) 继承本类, 所以门面自己**就是**一个 Workspace, 各协作对象拿到的 `ws`
就是那个门面。DoctorMixin / BoardSourceMixin 读的 `self.root` / `self.store` 也来自这里。

## 工作区写锁
`_workspace_lock` 是 fcntl.flock 排他锁, 由 `cli.main` 对会写盘的命令统一加, 命令自身不管锁。
"""
from __future__ import annotations

import contextlib
import fcntl
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Iterator, Optional, cast

from skeinlib.config import _cfg_backfill, _cfg_effective, _yaml_dump, _yaml_load, hooks_schema_errors
from skeinlib.errors import SkeinError
from skeinlib.hooks.runner import DBG, HookBlocked, _run_hooks
from skeinlib.model import S_DONE
from skeinlib.store import TaskStore
from skeinlib.worktree import git, worktrees_of

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


class Workspace:
    """一个 `.skein/` 工作区: 路径 + 生效配置 + 落盘层 + 阶段钩子。"""

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
        v = os.environ.get("CLAUDE_PLUGIN_OPTION_MAX_ACTIVE")
        if v and v.strip().isdigit():
            cfg["pools"]["work"] = int(v)
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

    def _dep_unfinished(self, dep: str) -> bool:
        # 归档即视为完成
        if self.store.archived_path(dep):
            return False
        f = self.tasks / dep / "task.json"
        if not f.exists():
            return False  # 未知 dep 不阻塞
        return cast(str, json.loads(f.read_text())["status"]) != S_DONE

    def _sub(self, t: dict[str, Any], sid: str) -> dict[str, Any]:
        for s in t.get("subtasks", []):
            if s["sid"] == sid:
                return cast(dict[str, Any], s)
        raise SkeinError(f"subtask 不存在: {t['id']}/{sid}")
