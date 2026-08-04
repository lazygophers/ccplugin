"""CLI 入口 — Typer 命令声明 + dispatch 表 + 工作区写锁。

写盘命令统一在这里加 `_workspace_lock` (fcntl.flock 排他), 纯读命令免锁 —— 锁的边界只在这一
处声明, 命令实现里不出现锁代码。新增写盘命令记得进 `MUTATING`, 漏了就是并发 read-modify-write。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

from types import SimpleNamespace
from typing import Annotated, Any, Optional

try:
    import typer
    from typer import _click
    from typer.core import TyperGroup
except ModuleNotFoundError:
    if os.environ.get("SKEIN_TYPER_BOOTSTRAPPED") != "1":
        env = dict(os.environ, SKEIN_TYPER_BOOTSTRAPPED="1")
        raise SystemExit(subprocess.run(["uv", "run", "python3", *sys.argv], env=env).returncode)
    raise

from skeinlib.hooks.runner import DBG, debug_enabled
from skeinlib.core.commands import Skein, _persist_bash_cwd_env, _workspace_lock
from skeinlib.task.model import PRD_TYPE_ALIAS


class AliasTyperGroup(TyperGroup):
    aliases = {"delete": "del", "rm": "del", "remove": "del"}

    def get_command(self, ctx: _click.Context, cmd_name: str) -> _click.Command | None:
        return super().get_command(ctx, self.aliases.get(cmd_name, cmd_name))


TASK_COMMANDS = {"create", "research", "plan", "confirm", "check", "finishing", "finish",
                 "priority", "estimate", "repos", "deps", "parent", "rename", "status", "show"}


app = typer.Typer(
    cls=AliasTyperGroup,
    help="SKEIN 任务管理引擎 — task 生命周期 + 看板 + 契约\n\ntask 编辑: task create → (research ⇄ plan) → confirm → check → finishing → finish; task rename/parent/deps/repos/estimate/priority/status",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode=None,  # docstring 里 [sid] 会被 rich 当样式标签吃掉, 关掉 markup 保留原文
)
task_app = typer.Typer(help="task 查看、编辑、状态变更", no_args_is_help=True)
config_app = typer.Typer(help="读写 .skein/config.yaml 配置", invoke_without_command=True)
prd_app = typer.Typer(help="读/写/追加/勾选 prd 章节 (目标/边界/User Stories/验收标准/验证方式/Testing Decisions)")

MUTATING = {"init", "setup", "create", "confirm", "research", "plan", "check", "finishing",
            "finish", "fmt", "clean",
            "contract", "repos", "deps", "parent", "estimate", "priority", "subtask", "claim",
            "prd", "del",
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
        "check": sk.lifecycle.check, "finishing": sk.lifecycle.finishing,
        "finish": sk.lifecycle.finish,
        "repos": sk.lifecycle.repos, "deps": sk.lifecycle.deps,
        "parent": sk.lifecycle.parent,
        "estimate": sk.lifecycle.estimate, "priority": sk.lifecycle.priority, "rename": sk.lifecycle.rename,
        "del": sk.lifecycle.del_,
        "claim": sk.scheduler.claim, "subtask": sk.scheduler.subtask,
        "ready": sk.query.ready,
        "status": sk.query.status, "list": sk.query.list_,
        "fmt": sk.artifacts.fmt, "prd": sk.artifacts.prd, "contract": sk.artifacts.contract,
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
    # 业务方法返回 dict → 统一 JSON 输出; 返回 None → 静默 (已自行输出或无输出)
    if isinstance(result, dict):
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
    kind: Annotated[str, typer.Option("--kind")] = "task",
    parent: Annotated[Optional[str], typer.Option("--parent")] = None,
    estimate: Annotated[Optional[float], typer.Option("--estimate")] = None,
    priority: Annotated[Optional[str], typer.Option("--priority")] = None,
) -> None:
    """登记新 task。"""
    _run("create", id=id, name=name, desc=desc, deps=deps, repos=repos, kind=kind, parent=parent,
         estimate=estimate, priority=priority)


@task_app.command("priority")
def priority(id: str, set_: Annotated[Optional[str], typer.Option("--set")] = None) -> None:
    """查/改 task 优先级。"""
    _run("priority", id=id, set=set_)


@task_app.command("estimate")
def estimate(id: str, set_: Annotated[Optional[str], typer.Option("--set")] = None) -> None:
    """查/填 task 预计工时。"""
    _run("estimate", id=id, set=set_)


@task_app.command("repos")
def repos(id: str, set_: Annotated[Optional[str], typer.Option("--set")] = None) -> None:
    """查/声明 task 目标子 git。"""
    _run("repos", id=id, set=set_)


@task_app.command("deps")
def deps(id: str, set_: Annotated[Optional[str], typer.Option("--set")] = None) -> None:
    """查/补 task 级前置 DAG。"""
    _run("deps", id=id, set=set_)


@task_app.command("parent")
def parent(id: str, set_: Annotated[Optional[str], typer.Option("--set")] = None) -> None:
    """查/改既有 task 的 parent 挂载。"""
    _run("parent", id=id, set=set_)


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
) -> None:
    """用户确认门。"""
    _run("confirm", id=id, summary=summary, approved=approved)


@task_app.command("check")
def check(id: str) -> None:
    """标记 task 进入检查阶段。"""
    _run("check", id=id)


@task_app.command("finishing")
def finishing(id: str) -> None:
    """检查中→收尾中。"""
    _run("finishing", id=id)


@task_app.command("finish")
def finish(id: str) -> None:
    """收束 task。"""
    _run("finish", id=id)


@app.command()
def fmt(id: str) -> None:
    """规范化 prd.md。"""
    _run("fmt", id=id)


def _delete(ctx: typer.Context, dry_run: bool = False) -> None:
    args = list(ctx.args)
    if len(args) < 1 or len(args) > 2:
        raise typer.BadParameter("del 用法: del <task_id> [subtask_sid]")
    task_id = args[0]
    subtask_sid = args[1] if len(args) == 2 else None
    _run("del", task_id=task_id, subtask_sid=subtask_sid, dry_run=dry_run)


@app.command("del", context_settings={"allow_extra_args": True, "ignore_unknown_options": False})
def del_(ctx: typer.Context, dry_run: Annotated[bool, typer.Option("--dry-run")] = False) -> None:
    """删 task 或单 subtask。"""
    _delete(ctx, dry_run)


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


@app.command("list")
def list_(status: Annotated[Optional[str], typer.Option("--status")] = None,
          json_: Annotated[bool, typer.Option("--json")] = False) -> None:
    """列所有 task。"""
    _run("list", status=status, json=json_)


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
    estimate: Annotated[Optional[str], typer.Option("--estimate")] = None,
    deps: Annotated[Optional[str], typer.Option("--deps")] = None,
    check: Annotated[Optional[str], typer.Option("--check")] = None,
    phase: Annotated[Optional[str], typer.Option("--phase")] = None,
    note: Annotated[Optional[str], typer.Option("--note")] = None,
    passed: Annotated[Optional[str], typer.Option("--passed")] = None,
    skills: Annotated[Optional[str], typer.Option("--skills")] = None,
) -> None:
    """单 task 内 subtask DAG 调度。

    用法: subtask <action> <tid> [sid]

    \b
    add   <tid> <sid> --name <str> --desc <str> --estimate <num> [--deps] [--skills]  登记→待处理
    claim <tid>                                                                         批量 ready→运行中
    start <tid> <sid>                                                                   单个 待处理/失败→运行中
    done  <tid> <sid> [--passed]                                                        运行中→已完成
    fail  <tid> <sid> [--note]                                                          运行中→失败
    check <tid> <sid> [--check]                                                         勾验收, 不改状态
    rename <tid> <sid> [--id] [--name]                                                   重命名 subtask
    ready <tid>                                                                         只读预览
    show  <tid> <sid>                                                                   单条详情
    list  <tid>                                                                         全表
    """
    args = list(ctx.args)
    if len(args) < 2 or len(args) > 3:
        raise typer.BadParameter("subtask 用法: subtask <action> <tid> [sid]")
    action, tid = args[0], args[1]
    sid = args[2] if len(args) == 3 else None
    if action not in ("add", "claim", "ready", "start", "check", "show", "rename", "done", "fail", "list"):
        raise typer.BadParameter("action 仅允许 add/claim/ready/start/check/show/rename/done/fail/list")
    if action in ("add", "start", "check", "show", "rename", "done", "fail") and not sid:
        raise typer.BadParameter(f"subtask {action} 需要 sid")
    if action == "rename":
        _run("rename", tid=tid, sid=sid, id=id, name=name)
        return
    if action == "add":
        missing = [flag for flag, value in (("--name", name), ("--desc", desc), ("--estimate", estimate)) if not value]
        if missing:
            raise typer.BadParameter(f"subtask add 必填: {', '.join(missing)} (sid/name/desc/estimate 缺一不可)")
    if phase not in (None, "exec", "research"):
        raise typer.BadParameter("phase 仅允许 exec/research")
    _run("subtask", action=action, tid=tid, sid=sid, name=name, desc=desc, estimate=estimate,
         deps=deps, check=check, phase=phase, note=note, passed=passed, skills=skills)


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


@prd_app.callback()
def prd() -> None:
    """PRD 章节操作。"""


def _prd_action(action: str, id: str, type_: str, list_: Optional[str]) -> None:
    if type_ not in PRD_TYPE_ALIAS:
        raise typer.BadParameter(f"--type 仅允许: {', '.join(PRD_TYPE_ALIAS)}")
    _run("prd", action=action, id=id, type=type_, list=list_)


@prd_app.command("read")
def prd_read(id: str, type_: Annotated[str, typer.Option("--type")]) -> None:
    """读章节正文。"""
    _prd_action("read", id, type_, None)


@prd_app.command("write")
def prd_write(id: str, type_: Annotated[str, typer.Option("--type")],
              list_: Annotated[str, typer.Option("--list")]) -> None:
    """整章清重建。"""
    _prd_action("write", id, type_, list_)


@prd_app.command("add")
def prd_add(id: str, type_: Annotated[str, typer.Option("--type")],
            list_: Annotated[str, typer.Option("--list")]) -> None:
    """追加条目。"""
    _prd_action("add", id, type_, list_)


@prd_app.command("check")
def prd_check(id: str, type_: Annotated[str, typer.Option("--type")],
              list_: Annotated[str, typer.Option("--list")]) -> None:
    """勾选条目。"""
    _prd_action("check", id, type_, list_)


@prd_app.command("uncheck")
def prd_uncheck(id: str, type_: Annotated[str, typer.Option("--type")],
                list_: Annotated[str, typer.Option("--list")]) -> None:
    """反勾选条目。"""
    _prd_action("uncheck", id, type_, list_)


def _strip_global_flags(argv: list[str]) -> tuple[list[str], bool, bool]:
    cli_debug = any(arg in ("-d", "--debug") for arg in argv)
    cli_json = any(arg in ("-j", "--json") for arg in argv)
    return [arg for arg in argv if arg not in ("-d", "--debug", "-j", "--json")], cli_debug, cli_json


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
        return ["task", *argv]
    return argv


def main() -> None:
    argv, cli_debug, cli_json = _strip_global_flags(sys.argv[1:])
    DBG.enable(cli_debug or debug_enabled(None))
    original_namespace = _namespace

    def namespace_with_json(cmd: str, **kwargs: object) -> SimpleNamespace:
        a = original_namespace(cmd, **kwargs)
        a.json = bool(getattr(a, "json", False) or cli_json)
        return a

    globals()["_namespace"] = namespace_with_json
    try:
        if not _run_hidden_command(argv):
            argv = _rewrite_legacy_task_args(argv)
            app(args=argv, prog_name="skein")
    finally:
        globals()["_namespace"] = original_namespace
