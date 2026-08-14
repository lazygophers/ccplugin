"""CLI 入口 — Typer 命令声明 + dispatch 表 + 工作区写锁。

写盘命令统一在这里加 `_workspace_lock` (fcntl.flock 排他), 纯读命令免锁 —— 锁的边界只在这一
处声明, 命令实现里不出现锁代码。新增写盘命令记得进 `MUTATING`, 漏了就是并发 read-modify-write。
"""
from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys

from types import SimpleNamespace
from typing import Annotated, Any, Optional

try:
    import typer
    from typer.core import TyperGroup
    # typer ≥0.12 把 click 封进内部 `_click` 包 (隔离 click 8.1/9 弃用噪声); 旧版 (<0.12)
    # 直接 re-export 顶层 `click`。`_click` 在旧版不存在会抛 ImportError (非 ModuleNotFoundError),
    # 两路都要兜住 —— `cannot import name '_click'` 正是用户旧全局 typer 报的错。
    try:
        from typer import _click  # typer ≥0.12
    except ImportError:
        import click as _click  # type: ignore[no-redef]  # typer <0.12 (顶层 click 即 typer 的 click)
except ImportError:
    # typer 整体缺失或内部结构异常 → 改用 uv 的隔离环境重跑 (那里按 requirements.txt 装齐)。
    # 注意异常类用 ImportError (ModuleNotFoundError 是其子类, 但反向不成立 —— 旧版 typer 缺
    # `_click` 抛的是 ImportError 而非 ModuleNotFoundError, 原代码只接后者导致 bootstrap 漏触发)。
    #
    # 命令行必须由 _bootstrap.uv_rerun_cmd 构造: 光 `uv run python3` 不带任何依赖声明, 子进程
    # 照样没有 typer, 只会原样再打一遍同一份 traceback, 看起来就像这条兜底根本没跑。
    if os.environ.get("SKEIN_TYPER_BOOTSTRAPPED") != "1":
        try:
            import _bootstrap  # scripts/ 由入口 (skein.py / spec.py) 置于 sys.path[0]
            env = dict(os.environ, SKEIN_TYPER_BOOTSTRAPPED="1")
            raise SystemExit(subprocess.run(_bootstrap.uv_rerun_cmd(sys.argv), env=env).returncode)
        except (OSError, ImportError):
            pass  # 没装 uv / 拿不到 _bootstrap — 落回原始 ImportError, 比「uv 找不到」好懂
    raise

from skeinlib.hooks.runner import DBG, debug_enabled
from skeinlib.core.commands import Skein, _persist_bash_cwd_env, _workspace_lock
from skeinlib.task.model import PRD_SECTIONS, PRD_TYPE_ALIAS, PRIORITIES, PRIORITY_DEFAULT, ESTIMATE_HINT


# 跨 typer 版本的 make_metavar 签名兼容 shim。给 stub 打补丁天然过不了 method-assign/call-arg,
# 这四条 ignore 是上游签名漂移的代价, 不是本仓类型债 —— 逐条限定 error code, 不开全局豁免。
if len(inspect.signature(typer.core.TyperOption.make_metavar).parameters) == 2:
    _typer_option_make_metavar = typer.core.TyperOption.make_metavar

    def _compatible_option_make_metavar(self: Any, ctx: Any = None) -> str:
        return _typer_option_make_metavar(self, ctx)

    typer.core.TyperOption.make_metavar = _compatible_option_make_metavar  # type: ignore[method-assign]

if len(inspect.signature(typer.core.TyperArgument.make_metavar).parameters) == 1:
    _typer_argument_make_metavar = typer.core.TyperArgument.make_metavar

    def _compatible_argument_make_metavar(self: Any, ctx: Any = None) -> str:
        return _typer_argument_make_metavar(self)  # type: ignore[call-arg]

    typer.core.TyperArgument.make_metavar = _compatible_argument_make_metavar  # type: ignore[method-assign,assignment]


# 报错文案自足化: click 默认只吐 `Error: ...` + `Try --help`, agent 拿不到正确写法, 只能再跑一次
# `--help` (审计实测: 12 个回合废在这上面)。这里在原文案后补该子命令的 usage 行与可用选项,
# 一次报错就够改对。挂在 UsageError.show 而非各命令内, 是因为参数级报错由 click 统一抛出。
_orig_usage_show = _click.exceptions.UsageError.show


def _usage_show(self: Any, file: Any = None) -> None:
    _orig_usage_show(self, file)
    ctx = getattr(self, "ctx", None)
    if ctx is None:
        return
    out = file or sys.stderr
    try:
        if hasattr(ctx.command, "list_commands"):
            commands = sorted(ctx.command.list_commands(ctx))
            if commands:
                _click.echo("可用子命令: " + " ".join(commands), file=out)
        else:
            opts = sorted({o for p in ctx.command.get_params(ctx)
                           for o in getattr(p, "opts", []) if o.startswith("--")})
            if opts:
                _click.echo("可用选项: " + " ".join(opts), file=out)
    except Exception:  # 纯提示增强, 任何异常都不该盖掉原始报错
        pass


_click.exceptions.UsageError.show = _usage_show  # type: ignore[method-assign]


def _set_value(set_: Optional[str], value: Optional[str]) -> Optional[str]:
    """`--set X` 与位置写法 `<id> X` 等价。

    agent 高频写成位置参数 (`task estimate t1 15`), 原本只报 `Got unexpected extra argument(s)`,
    既不说该用 `--set` 也没别的线索。两种写法都收, 同时给 `--set` 优先。
    """
    return set_ if set_ is not None else value


class AliasTyperGroup(TyperGroup):
    aliases = {"delete": "del", "rm": "del", "remove": "del"}

    def get_command(self, ctx: _click.Context, cmd_name: str) -> _click.Command | None:
        return super().get_command(ctx, self.aliases.get(cmd_name, cmd_name))


class TaskTyperGroup(TyperGroup):
    """task 子命令组 —— 未知的「通用改写」命令给出状态机指引。

    `task update --status active` 是最自然的猜测 (多数 CLI 都这么设计), 但 skein 的状态变更
    是逐阶段命令。裸一句 "No such command 'update'" 换来的只是第二次瞎猜。
    """

    _STATE_GUESSES = {"update", "set", "modify", "edit", "transition", "move"}

    def get_command(self, ctx: _click.Context, cmd_name: str) -> _click.Command | None:
        cmd = super().get_command(ctx, cmd_name)
        if cmd is None and cmd_name in self._STATE_GUESSES:
            # _click 是 typer 的内部 shim, 只 re-export 了 ClickException —— 用它, 别用
            # UsageError (旧/新版 typer 都不保证暴露)。
            raise _click.ClickException(
                f"task 无 {cmd_name} 命令 — 状态变更走逐阶段命令: "
                "confirm (待处理→进行中) / research+plan (待处理⇄调研中) / "
                "check (进行中→检查中) / revert (检查中→待处理) / "
                "finishing (检查中→收尾中) / finish (收尾中→已完成); "
                "改字段用 task rename / priority / estimate / deps / repos")
        return cmd


TASK_COMMANDS = {"create", "research", "plan", "confirm", "check", "revert", "finishing", "finish",
                 "priority", "estimate", "repos", "deps", "rename", "status", "show"}

# prd --type 的合法值提示 — 中英 alias 都收, help 里只列英文短名 (够 agent 用且不撑爆一行)
_PRD_TYPE_HELP = "章节: goal|scope|stories|acceptance|verification|testing (中文段名亦可); write/add 可重复传并一次写多段"
# check/uncheck 的 --list 与 write/add 的 --list 同名但语义相反 (匹配 vs 内容) —— 必须点破
_PRD_MATCH_HELP = "要勾的条目原文子串 (先 `prd read` 看原文取一段唯一子串); 也收纯数字 = 章节内第 N 条"


app = typer.Typer(
    cls=AliasTyperGroup,
    help="SKEIN 任务管理引擎 — task 生命周期 + 看板 + 契约\n\ntask 编辑: task create → (research ⇄ plan) → confirm → check → revert/finishing → finish; task rename/parent/deps/repos/estimate/priority/status",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode=None,  # docstring 里 [sid] 会被 rich 当样式标签吃掉, 关掉 markup 保留原文
)
task_app = typer.Typer(cls=TaskTyperGroup, help="task 查看、编辑、状态变更", no_args_is_help=True)
config_app = typer.Typer(help="读写 .skein/config.yaml 配置", invoke_without_command=True)
prd_app = typer.Typer(help="读/写/追加/勾选 prd 章节 (目标/边界/验收标准)")
design_app = typer.Typer(help="读/写 design.md 测试接缝段 (confirm 硬门校验的那段)")

MUTATING = {"init", "setup", "create", "confirm", "research", "plan", "check", "revert", "finishing",
            "finish", "fmt", "clean",
            "contract", "repos", "deps", "estimate", "priority", "subtask", "claim",
            "prd", "design", "flow", "del",
            "rename", "config"}


def _namespace(cmd: str, **kwargs: object) -> SimpleNamespace:
    data = {"cmd": cmd, "json": False}
    data.update(kwargs)
    return SimpleNamespace(**data)


def _dispatch(a: SimpleNamespace) -> None:
    if getattr(a, "cmd", None) == "session-context":
        _persist_bash_cwd_env()
        Skein().session_context()
        return
    sk = Skein()
    dispatch = {
        "init": sk.admin.init, "setup": sk.admin.setup, "config": sk.admin.config_cmd,
        "clean": sk.admin.clean, "board": sk.admin.board,
        "create": sk.lifecycle.create, "confirm": sk.lifecycle.confirm,
        "research": sk.lifecycle.research, "plan": sk.lifecycle.plan,
        "check": sk.lifecycle.check, "revert": sk.lifecycle.revert, "finishing": sk.lifecycle.finishing,
        "finish": sk.lifecycle.finish,
        "repos": sk.lifecycle.repos, "deps": sk.lifecycle.deps,
        "estimate": sk.lifecycle.estimate, "priority": sk.lifecycle.priority, "rename": sk.lifecycle.rename,
        "del": sk.lifecycle.del_,
        "claim": sk.scheduler.claim, "flow": sk.scheduler.flow, "subtask": sk.scheduler.subtask,
        "ready": sk.query.ready,
        "status-overview": sk.query.status_overview,
        "status": sk.query.status, "list": sk.query.list_,
        "fmt": sk.artifacts.fmt, "prd": sk.artifacts.prd, "design": sk.artifacts.design,
        "contract": sk.artifacts.contract,
        "serve": sk.serve, "doctor": sk.doctor,
    }
    DBG.rule(f"skein {a.cmd}")
    DBG.kv({k: v for k, v in vars(a).items() if k not in ("cmd", "debug") and v not in (None, False)}, title="参数")
    if a.cmd in MUTATING:
        with _workspace_lock(sk.dir / ".lock"):
            result = dispatch[a.cmd](a)  # type: ignore[arg-type]
    else:
        result = dispatch[a.cmd](a)  # type: ignore[arg-type]
    DBG.log(f"✓ {a.cmd} 完成", style="bold green")
    # 业务方法返回 dict → 统一 JSON 输出; 返回 None → 静默 (已自行输出或无输出)。
    # -p/--pretty: dict 改走 rich 面板渲染 (人读); 非 dict 返回值不受影响。
    if isinstance(result, dict):
        if getattr(a, "pretty", False):
            _pretty_print(a.cmd, result)
        else:
            print(json.dumps(result, ensure_ascii=False))
    elif result is not None:
        # 非 dict 返回值 (如 str) → 包装
        print(json.dumps({"data": result}, ensure_ascii=False))


def _run(cmd: str, **kwargs: object) -> None:
    _dispatch(_namespace(cmd, **kwargs))


@app.callback()
def root() -> None:
    """SKEIN 任务管理引擎。"""


@app.command()
def init() -> None:
    """初始化 .skein/ 工作区 (幂等)。"""
    _run("init")


@app.command()
def setup(full: bool = typer.Option(False, "--full"), no_web: bool = typer.Option(False, "--no-web")) -> None:
    """初始化 + trellis 迁移。"""
    _run("setup", full=full, no_web=no_web)


@task_app.command("create")
def create(
    id: Annotated[str, typer.Argument(help="可读 id")],
    name: Annotated[str, typer.Option("--name", help="task 标题")],
    desc: Annotated[str, typer.Option("--desc", help="一句话描述")],
    deps: Annotated[Optional[str], typer.Option("--deps")] = None,
    repos: Annotated[Optional[str], typer.Option("--repos")] = None,
    estimate: Annotated[Optional[str], typer.Option("--estimate", help=ESTIMATE_HINT)] = None,
    priority: Annotated[Optional[str], typer.Option(
        "--priority", help=f"仅允许: {', '.join(PRIORITIES)} (默认 {PRIORITY_DEFAULT})")] = None,
    like: Annotated[Optional[str], typer.Option(
        "--like", help="拿既有 task (含已完成的) 当模板: 克隆 prd/design/subtask 骨架, 状态全重置")] = None,
) -> None:
    """登记新 task。"""
    _run("create", id=id, name=name, desc=desc, deps=deps, repos=repos,
         estimate=estimate, priority=priority, like=like)


# 下面五条同构: `<id>` 后省略值 = 查, 给值 = 改。值可走 `--set` 也可直接跟在 id 后 (见 _set_value)。
_SET_ARG = typer.Argument(metavar="[VALUE]", help="等价 --set; 省略则为只读查询")


@task_app.command("priority")
def priority(id: str, value: Annotated[Optional[str], _SET_ARG] = None,
             set_: Annotated[Optional[str], typer.Option(
                 "--set", help=f"仅允许: {', '.join(PRIORITIES)}")] = None) -> None:
    """查/改 task 优先级。"""
    _run("priority", id=id, set=_set_value(set_, value))


@task_app.command("estimate")
def estimate(id: str, value: Annotated[Optional[str], _SET_ARG] = None,
             set_: Annotated[Optional[str], typer.Option(
                 "--set", help=ESTIMATE_HINT)] = None) -> None:
    """查/填 task 预计工时。"""
    _run("estimate", id=id, set=_set_value(set_, value))


@task_app.command("repos")
def repos(id: str, value: Annotated[Optional[str], _SET_ARG] = None,
          set_: Annotated[Optional[str], typer.Option("--set")] = None) -> None:
    """查/声明 task 目标子 git。"""
    _run("repos", id=id, set=_set_value(set_, value))


@task_app.command("deps")
def deps(id: str, value: Annotated[Optional[str], _SET_ARG] = None,
         set_: Annotated[Optional[str], typer.Option("--set")] = None) -> None:
    """查/补 task 级前置 DAG。"""
    _run("deps", id=id, set=_set_value(set_, value))


@task_app.command("research")
def research(id: str) -> None:
    """待处理→调研中。"""
    _run("research", id=id)


@task_app.command("plan")
def plan(id: str) -> None:
    """调研中→待处理。"""
    _run("plan", id=id)


@task_app.command("confirm")
def confirm(
    id: str,
    summary: Annotated[bool, typer.Option("--summary")] = False,
    approved: Annotated[bool, typer.Option("--approved")] = False,
    unattended: Annotated[bool, typer.Option(
        "--unattended", help="无人值守放行 (cron/CI); 需先 config set confirm.unattended true")] = False,
    force: Annotated[bool, typer.Option("--force", help="跳过 planning 就绪门")] = False,
) -> None:
    """用户确认门。"""
    _run("confirm", id=id, summary=summary, approved=approved, unattended=unattended, force=force)


@task_app.command("check")
def check(id: str) -> None:
    """标记 task 进入检查阶段。"""
    _run("check", id=id)


@task_app.command("revert")
def revert(id: str) -> None:
    """检查中→待处理 (回退到规划)。"""
    _run("revert", id=id)


@task_app.command("finishing")
def finishing(id: str) -> None:
    """检查中→收尾中。"""
    _run("finishing", id=id)


@task_app.command("finish")
def finish(id: str, force: Annotated[bool, typer.Option(
        "--force", help="跳过状态与 gate 门, 仍执行完整收尾")] = False) -> None:
    """收束 task。"""
    _run("finish", id=id, force=force)


@app.command()
def fmt(id: str) -> None:
    """规范化 prd.md。"""
    _run("fmt", id=id)


def _delete(ctx: typer.Context, dry_run: bool = False, force: bool = False) -> None:
    args = list(ctx.args)
    if len(args) < 1 or len(args) > 2:
        raise typer.BadParameter("del 用法: del <task_id> [subtask_sid]")
    task_id = args[0]
    subtask_sid = args[1] if len(args) == 2 else None
    _run("del", task_id=task_id, subtask_sid=subtask_sid, dry_run=dry_run, force=force)


@app.command("del", context_settings={"allow_extra_args": True, "ignore_unknown_options": False})
def del_(ctx: typer.Context, dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
         force: Annotated[bool, typer.Option("--force")] = False) -> None:
    """删 task 或单 subtask。"""
    _delete(ctx, dry_run, force)


@task_app.command("rename")
def task_rename(tid: str,
                id: Annotated[Optional[str], typer.Option("--id")] = None,
                name: Annotated[Optional[str], typer.Option("--name")] = None) -> None:
    """重命名 task。"""
    _run("rename", tid=tid, sid=None, id=id, name=name)


@app.command()
def clean(days: Annotated[Optional[int], typer.Option("--days")] = None) -> None:
    """归档完成超保留期的 task。"""
    _run("clean", days=days)


@app.command()
def ready() -> None:
    """脚本算可启动 task 批。"""
    _run("ready")


@app.command("status")
def status_overview(pretty: Annotated[bool, typer.Option(
        "--pretty", help="rich 渲染人读输出 (默认 JSON)")] = False) -> None:
    """全局运行态概览: 两池占用 + 执行中 subtask + 状态统计。

    单 task 详情走 `skein task status <tid>`。
    """
    _run("status-overview", pretty=pretty)


@app.command()
def claim(
    phase: Annotated[Optional[str], typer.Argument(help="exec/check; 省略=同时返回两路")] = None,
    task: Annotated[Optional[str], typer.Option("--task")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """全局跨 task 认领批。"""
    if phase not in (None, "exec", "check"):
        raise typer.BadParameter("phase 仅允许 exec/check")
    _run("claim", phase=phase, task=task, dry_run=dry_run)


@app.command()
def flow(
    action: Annotated[str, typer.Argument(help="run")],
    task: Annotated[Optional[str], typer.Option("--task")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """自动认领并输出 Agent 派发指令。"""
    if action != "run":
        raise typer.BadParameter("flow action 仅允许 run")
    _run("flow", action=action, task=task, dry_run=dry_run)


@app.command("list")
def list_(status: Annotated[Optional[str], typer.Option(
              "--status", help="plan/research/exec/check/finishing/finish/done (中文名亦可), "
                               "open/plan=待处理阶段, unfinished=全部未完成, all=不筛; 逗号分隔可多选")] = None,
          json_: Annotated[bool, typer.Option("--json")] = False) -> None:
    """列所有 task。"""
    _run("list", status=status, json=json_)


# `skein task list` 是最自然的猜测 (task 组里其余全是 task 子命令), 但真命令在顶层。
# 与其让调用方吃一次 "No such command 'list'", 不如在 task 组里转发同一个实现。
task_app.command("list")(list_)


@app.command()
def doctor(quality: Annotated[bool, typer.Option("--quality", "-Q")] = False) -> None:
    """纯脚本体检。"""
    _run("doctor", quality=quality)


@app.command()
def board() -> None:
    """渲染 .skein/task.md 看板。"""
    _run("board")


@app.command()
def serve(auto: Annotated[bool, typer.Option("--auto")] = False,
          open_: Annotated[bool, typer.Option("--open")] = False) -> None:
    """持久看板 http 服务。"""
    _run("serve", auto=auto, open_browser=open_)


@app.command()
def contract(id: str, add: Annotated[Optional[str], typer.Option("--add")] = None) -> None:
    """查/加 task 契约。"""
    _run("contract", id=id, add=add)


@task_app.command("status")
def task_status(tid: str, json_: Annotated[bool, typer.Option("--json")] = False) -> None:
    """查 task 态 + subtask 汇总。"""
    _run("status", tid=tid, sid=None, json=json_)


@task_app.command("show")
def task_show(tid: str, json_: Annotated[bool, typer.Option("--json")] = False) -> None:
    """查 task 详情。"""
    _run("status", tid=tid, sid=None, json=json_)


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": False})
def subtask(
    ctx: typer.Context,
    id: Annotated[Optional[str], typer.Option("--id")] = None,
    name: Annotated[Optional[str], typer.Option("--name")] = None,
    desc: Annotated[Optional[str], typer.Option("--desc")] = None,
    estimate: Annotated[Optional[str], typer.Option("--estimate", help=ESTIMATE_HINT)] = None,
    deps: Annotated[Optional[str], typer.Option("--deps")] = None,
    check: Annotated[Optional[list[str]], typer.Option(
        "--check", help="验收标准, 分号分隔多条; 可重复传, 各段累加")] = None,
    phase: Annotated[Optional[str], typer.Option("--phase")] = None,
    repo: Annotated[Optional[str], typer.Option("--repo", help="多 repo task 的目标 repo")] = None,
    note: Annotated[Optional[str], typer.Option("--note")] = None,
    passed: Annotated[Optional[str], typer.Option("--passed")] = None,
    skills: Annotated[Optional[str], typer.Option("--skills")] = None,
    status_filter: Annotated[Optional[str], typer.Option(
        "--status", help="list 过滤: pending/running/done/failed (仅 list 动作收)")] = None,
) -> None:
    """单 task 内 subtask DAG 调度。

    用法: subtask <action> <tid> [sid]

    \b
    add   <tid> <sid> --name <str> --desc <str> --estimate <num> [--deps] [--check] [--phase] [--skills] [--repo]  登记→待处理
    claim <tid>                                                                         批量 ready→运行中
    start <tid> <sid>                                                                   单个 待处理/失败→运行中
    done  <tid> <sid>                                                                   运行中→已完成 (验收全过)
    fail  <tid> <sid> [--note]                                                          运行中→失败
    check <tid> <sid> --passed <序号|all|none>                                          勾验收, 不改状态
    rename <tid> <sid> [--id] [--name]                                                   重命名 subtask
    ready <tid>                                                                         只读预览
    show  <tid> <sid>                                                                   单条详情
    list  <tid> [--status]                                                              全表; tid=all 跨 task 合并, --status 过滤状态
    """
    args = list(ctx.args)
    if len(args) < 2 or len(args) > 3:
        raise typer.BadParameter("subtask 用法: subtask <action> <tid> [sid]")
    action, tid = args[0], args[1]
    sid = args[2] if len(args) == 3 else None
    if action not in ("add", "claim", "ready", "start", "check", "show", "rename", "done", "fail", "list"):
        raise typer.BadParameter("action 仅允许 add/claim/ready/start/check/show/rename/done/fail/list")
    if action in ("add", "start", "check", "show", "rename", "done", "fail") and not sid:
        # 报错带上该 action 的完整用法 —— 只说「需要 sid」的话, agent 还得再跑一次 --help 才知道
        # sid 该摆在 tid 后面 (实测撞过两次)
        usage = {"add": "subtask add <tid> <sid> --name <str> --desc <str> --estimate <num> [--deps] [--check] [--phase] [--skills] [--repo]",
                 "check": "subtask check <tid> <sid> --passed <序号|all|none>",
                 "rename": "subtask rename <tid> <sid> [--id <新sid>] [--name <新名>]",
                 "done": "subtask done <tid> <sid>",
                 "fail": "subtask fail <tid> <sid> --note <原因>",
                 }.get(action, f"subtask {action} <tid> <sid>")
        raise typer.BadParameter(f"subtask {action} 需要 sid — 用法: {usage}")
    if action == "rename":
        _run("rename", tid=tid, sid=sid, id=id, name=name)
        return
    if action == "add":
        missing = [flag for flag, value in (("--name", name), ("--desc", desc), ("--estimate", estimate)) if not value]
        if missing:
            raise typer.BadParameter(f"subtask add 必填: {', '.join(missing)} (sid/name/desc/estimate 缺一不可)")
    if phase not in (None, "exec", "research"):
        raise typer.BadParameter("phase 仅允许 exec/research")
    if status_filter not in (None, "pending", "running", "done", "failed"):
        raise typer.BadParameter("--status 仅允许 pending/running/done/failed")
    _run("subtask", action=action, tid=tid, sid=sid, name=name, desc=desc, estimate=estimate,
         deps=deps, check=check, phase=phase, repo=repo, note=note, passed=passed, skills=skills,
         status_filter=status_filter)


app.add_typer(task_app, name="task")
app.add_typer(config_app, name="config")


@task_app.callback()
def task() -> None:
    """task 查看、编辑、状态变更。"""


@config_app.callback(invoke_without_command=True)
def config(ctx: typer.Context, json_: Annotated[bool, typer.Option("--json")] = False) -> None:
    """无参展示全部配置。"""
    if ctx.invoked_subcommand is None:
        _run("config", action=None, json=json_, key=None, value=None)


@config_app.command("set")
def config_set(key: str, value: str) -> None:
    """写单个配置键。"""
    _run("config", action="set", key=key, value=value, json=False)


@config_app.command("reset")
def config_reset() -> None:
    """重置全部配置为默认值。"""
    _run("config", action="reset", key=None, value=None, json=False)


app.add_typer(prd_app, name="prd")
app.add_typer(design_app, name="design")


@prd_app.callback()
def prd() -> None:
    """PRD 章节操作。"""


@design_app.callback()
def design() -> None:
    """design.md 测试接缝段操作。"""


@design_app.command("seam")
def design_seam(id: str, list_: Annotated[str, typer.Option(
        "--list", help="接缝条目, \\n 分隔多条; 整段清重建 (同 prd write 语义)")]) -> None:
    """写 design.md 测试接缝段 (confirm 硬门)。"""
    _run("design", action="seam", id=id, list=list_)


@design_app.command("read")
def design_read(id: str) -> None:
    """读 design.md 测试接缝段。"""
    _run("design", action="read", id=id, list=None)


def _prd_action(action: str, id: str, type_: str, list_: Optional[str]) -> None:
    if type_ not in PRD_TYPE_ALIAS:
        raise typer.BadParameter(f"--type 仅允许: {', '.join(PRD_TYPE_ALIAS)}")
    _run("prd", action=action, id=id, type=type_, list=list_)


def _merge_extra(lists: list[str], extra: Optional[list[str]]) -> list[str]:
    """`--list "a" "b" "c"` 里的裸位置参数并入最后一个 `--list` 那一段。

    click 的 `--list` 只吃一个值, 余下的落成位置参数直接报 unexpected extra argument, 逼调用方
    拆成一条一次 —— 而 write 是整章清重建, 拆开写等于一条条把前面的清掉。
    """
    if not extra:
        return lists
    if not lists:
        raise typer.BadParameter(f"多出的位置参数 {extra} 无 --list 可并入 — 先写 --list")
    return [*lists[:-1], "\n".join([lists[-1], *extra])]


def _prd_pairs(action: str, id: str, types: list[str], lists: list[str]) -> None:
    """`--type`/`--list` 成对重复 = 一回合写多章。

    PRD 各段原本要逐段调用 (审计: 35 个 task 摊了 200 次 prd 写)。成对重复后一次写完,
    循环内逐段落盘 + 逐段回显, 语义与分七次调用完全一致。
    """
    if len(types) != len(lists):
        raise typer.BadParameter(
            f"--type 与 --list 必须成对: 收到 {len(types)} 个 --type, {len(lists)} 个 --list")
    for type_, list_ in zip(types, lists):
        _prd_action(action, id, type_, list_)


@prd_app.command("read")
def prd_read(id: str, type_: Annotated[Optional[str], typer.Option(
        "--type", help=f"{_PRD_TYPE_HELP}; 省略 = 全文")] = None) -> None:
    """读章节正文 (省略 --type 读全文)。"""
    if type_ is None:
        _run("prd", action="read", id=id, type=None, list=None)
        return
    _prd_action("read", id, type_, None)


@prd_app.command("write")
def prd_write(id: str, type_: Annotated[list[str], typer.Option("--type", help=_PRD_TYPE_HELP)],
              list_: Annotated[list[str], typer.Option("--list")],
              extra: Annotated[Optional[list[str]], typer.Argument(
                  help="`--list` 后多写的条目, 并入最后一个 --list 那一段")] = None) -> None:
    """整章清重建 (--type/--list 可成对重复, 一回合写多章)。"""
    _prd_pairs("write", id, type_, _merge_extra(list_, extra))


@prd_app.command("add")
def prd_add(id: str, type_: Annotated[list[str], typer.Option("--type", help=_PRD_TYPE_HELP)],
            list_: Annotated[list[str], typer.Option("--list")],
            extra: Annotated[Optional[list[str]], typer.Argument(
                help="`--list` 后多写的条目, 并入最后一个 --list 那一段")] = None) -> None:
    """追加条目 (--type/--list 可成对重复, 一回合写多章)。"""
    _prd_pairs("add", id, type_, _merge_extra(list_, extra))


@prd_app.command("check")
def prd_check(id: str, type_: Annotated[str, typer.Option("--type", help=_PRD_TYPE_HELP)],
              list_: Annotated[str, typer.Option("--list", help=_PRD_MATCH_HELP)]) -> None:
    """勾选条目 (--list 传条目原文子串, 非序号)。"""
    _prd_action("check", id, type_, list_)


@prd_app.command("uncheck")
def prd_uncheck(id: str, type_: Annotated[str, typer.Option("--type", help=_PRD_TYPE_HELP)],
                list_: Annotated[str, typer.Option("--list", help=_PRD_MATCH_HELP)]) -> None:
    """反勾选条目 (--list 传条目原文子串, 非序号)。"""
    _prd_action("uncheck", id, type_, list_)


def _strip_global_flags(argv: list[str]) -> tuple[list[str], bool, bool, bool]:
    cli_debug = any(arg in ("-d", "--debug") for arg in argv)
    cli_json = any(arg in ("-j", "--json") for arg in argv)
    cli_pretty = any(arg in ("-p", "--pretty") for arg in argv)
    return ([arg for arg in argv if arg not in ("-d", "--debug", "-j", "--json", "-p", "--pretty")],
            cli_debug, cli_json, cli_pretty)


def _pretty_value(v: Any, indent: str = "  ") -> str:
    """任意 CLI 结果值 → rich markup 字符串 (dict 多行缩进 / list 分块 / 标量直出)。"""
    if v is None:
        return "[dim]-[/dim]"
    if isinstance(v, bool):
        return "[green]✓[/green]" if v else "[dim]✗[/dim]"
    if isinstance(v, str):
        return v if v else "[dim](空)[/dim]"
    if isinstance(v, dict):
        if not v:
            return "[dim](空)[/dim]"
        sep = "\n" + indent
        return sep.join(f"[cyan]{k}[/cyan]: {_pretty_value(x, indent + '  ')}"
                        for k, x in v.items())
    if isinstance(v, list):
        if not v:
            return "[dim](空)[/dim]"
        if all(not isinstance(x, (dict, list)) for x in v):
            return ", ".join(_pretty_value(x, indent) for x in v)
        sep = "\n" + indent[:-2] + "[dim]────────[/dim]\n" + indent[:-2]
        return sep.join(_pretty_value(x, indent) for x in v)
    return str(v)


def _pretty_print(cmd: str, data: dict) -> None:
    """dict 结果 → rich 面板渲染 (全局 -p/--pretty 时替代 JSON print)。"""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("key", style="cyan", no_wrap=True)
    table.add_column("value")
    for k, v in data.items():
        table.add_row(str(k), _pretty_value(v))
    Console().print(Panel.fit(table, title=f"skein {cmd}", border_style="blue"))


def _run_hidden_command(argv: list[str]) -> bool:
    if argv == ["session-context"]:
        _run("session-context")
        return True
    return False


def _rewrite_legacy_task_args(argv: list[str]) -> list[str]:
    if argv[:1] == ["state"]:
        return ["task", *argv[1:]]
    if argv[:1] == ["rename"] and len(argv) >= 3 and not argv[2].startswith("-"):
        return ["subtask", "rename", *argv[1:]]
    if argv[:1] == ["status"] and len(argv) >= 3:
        return ["subtask", "show", *argv[1:]]
    if argv and argv[0] in TASK_COMMANDS:
        # `skein status` / `skein status --pretty` (仅跟 flag 无位置参数) = 顶层全局运行态概览,
        # 不转发; 带位置参数 `skein status <tid>` 仍转 task status (legacy)
        if not (argv[0] == "status"
                and all(x.startswith("-") for x in argv[1:])):
            return ["task", *argv]
    return argv


def main() -> None:
    from skeinlib.gitignore.preflight import run_preflight
    run_preflight()
    argv, cli_debug, cli_json, cli_pretty = _strip_global_flags(sys.argv[1:])
    DBG.enable(cli_debug or debug_enabled(None))
    original_namespace = _namespace

    def namespace_with_flags(cmd: str, **kwargs: object) -> SimpleNamespace:
        a = original_namespace(cmd, **kwargs)
        a.json = bool(getattr(a, "json", False) or cli_json)
        # 全局 -p/--pretty: 各命令的 pretty flag (如 status) 局部值为先, 全局补真
        a.pretty = bool(getattr(a, "pretty", False) or cli_pretty)
        return a

    globals()["_namespace"] = namespace_with_flags
    try:
        if not _run_hidden_command(argv):
            argv = _rewrite_legacy_task_args(argv)
            app(args=argv, prog_name="skein")
    finally:
        globals()["_namespace"] = original_namespace
