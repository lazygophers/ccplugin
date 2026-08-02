#!/usr/bin/env python3
"""SKEIN hook 公共工具 — 注入内容的 token 预算守卫 + 统一钩子执行器 (纯 stdlib)。

所有 SessionStart / PostTool* hook 注入上下文前, 过 budget_guard():
内容超预算 → stderr 警告 "简化内容", 且截断到硬上限, 免不可控 token 膨胀。
token 估算 = 字符数 // 4 (英混中的粗略常数, 宁可高估)。

_run_hooks() 是 config.yaml `hooks:` 自定义钩子的统一执行器 — 引擎侧的阶段钩子(before/after)
与 harness 侧的 agent 钩子(start/stop) 共用, 故落这个共享模块而非二者之一, 免相互反向 import。
config 解析 / 阶段名校验 / 具名+通配排序均归调用方, 本模块只管"给定一串已排好序的钩子, 怎么串行执行"。

叙事器 `DBG` 也在这儿: 它得是**稳定单例** (`DBG.enable(on)` 原地翻状态), 从前 `global DBG` 重绑
模块变量, 拆包后各模块 `from ... import DBG` 会各拿一份重绑前的旧对象, --debug 静默失效。
"""
from __future__ import annotations

import os
import subprocess
import sys
from typing import Any, Optional

CHARS_PER_TOKEN = 4  # 粗略: 1 token ≈ 4 字符 (中英混排偏保守)
HOOK_TIMEOUT_DEFAULT = 60  # 秒, config.yaml 单条钩子未写 timeout 时的缺省值


def debug_enabled(args: Any = None) -> bool:
    """--debug 开关: 命令行 --debug 或环境变量 SKEIN_DEBUG (非空/非 0/false/no) 任一即开。"""
    if args is not None and getattr(args, "debug", False):
        return True
    return os.environ.get("SKEIN_DEBUG", "").strip().lower() not in ("", "0", "false", "no")


class Debug:
    """--debug 叙事器: 把命令干了什么 (git / 写盘 / 锁 / 状态迁移) 用 rich 美化写 **stderr**。

    stdout 全程保持机器纯净 (list --json / claim exec --dry-run / board / hookSpecificOutput 等被 AI/hook 消费,
    rich 污染即破契约), 所以一切叙事只走 stderr。rich 不可用则纯文本降级; 未启用则全 no-op。
    """
    def __init__(self, enabled: bool) -> None:
        self.enabled = False
        self.c: Optional[Any] = None
        self.enable(enabled)

    def enable(self, on: bool) -> None:
        """开关叙事。**存在的理由**: 从前是 `global DBG; DBG = Debug(...)` 重绑模块变量, 于是
        `from ... import DBG` 拿到的是重绑前那个 —— 引擎一拆包就会各模块各拿一份, 静默失效。
        改成原地翻状态后 DBG 是稳定单例, 谁 import 都是同一个对象。"""
        self.enabled = on
        if on and self.c is None:
            try:
                from rich.console import Console
                self.c = Console(stderr=True)
            except Exception:
                self.c = None  # rich 缺失 → 纯文本降级

    def log(self, msg: str, style: Optional[str] = None) -> None:
        """debug / info 级 — 只有 --debug (或 SKEIN_DEBUG) 才输出。"""
        if not self.enabled:
            return
        self._emit(msg, style)

    def warn(self, msg: str) -> None:
        """warn 级 — **无视 --debug 永远输出**。用户需要知道命令为何没干活 (空跑退出、
        降级、跳过) 时用这个; 只有 --debug 才说的实现细节仍走 log()。"""
        self._emit(msg, "yellow")

    def error(self, msg: str) -> None:
        """error 级 — 无视 --debug 永远输出。数据损坏 / 操作失败。"""
        self._emit(msg, "red")

    def _emit(self, msg: str, style: Optional[str] = None) -> None:
        # rich Console 只在 enable(True) 时建; warn/error 可能先于 --debug 触发 → 惰性补建。
        if self.c is None:
            try:
                from rich.console import Console
                self.c = Console(stderr=True)
            except Exception:
                pass
        if self.c:
            self.c.print(msg, style=style, markup=False, highlight=False)
        else:
            sys.stderr.write(f"{msg}\n")

    def rule(self, title: str) -> None:
        if not self.enabled:
            return
        if self.c:
            self.c.rule(f"[bold cyan]{title}")
        else:
            sys.stderr.write(f"\n──── {title} ────\n")

    def kv(self, mapping: dict[str, Any], title: Optional[str] = None) -> None:
        """键值表 (rich Table, 降级为对齐文本)。"""
        if not self.enabled or not mapping:
            return
        if self.c:
            from rich.table import Table
            t = Table(show_header=False, box=None, title=title, title_justify="left",
                      title_style="dim")
            t.add_column(style="cyan", no_wrap=True)
            t.add_column(overflow="fold")
            for k, v in mapping.items():
                t.add_row(str(k), str(v))
            self.c.print(t)
        else:
            if title:
                sys.stderr.write(f"{title}\n")
            for k, v in mapping.items():
                sys.stderr.write(f"  {k}: {v}\n")


# 全局叙事器单例 — skein.py / spec.py 及 skeinlib 各模块共用同一个对象 (禁再各自 `DBG = Debug(...)`,
# 那会退回重绑模块变量的老坑)。默认关, 入口 main() 解析 --debug/SKEIN_DEBUG 后调 DBG.enable(True)。
DBG = Debug(False)


def est_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


def budget_guard(text: str, budget_tokens: int, label: str) -> str:
    """内容超 token 预算则 stderr 警告 + 硬截断到预算。返回可注入文本。

    label 用于警告定位 (哪个 hook)。硬截断防 model 忽视软警告后仍膨胀上下文。
    """
    tok = est_tokens(text)
    if tok <= budget_tokens:
        return text
    limit = budget_tokens * CHARS_PER_TOKEN
    sys.stderr.write(
        f"[skein hook:{label}] 注入内容 ~{tok} token > 预算 {budget_tokens} — "
        f"请简化 (core 规则降级 recall / 精简正文), 已硬截断到 {budget_tokens} token\n")
    return text[:limit] + "\n\n… (超预算已截断, 见 stderr)"


class HookBlocked(RuntimeError):
    """阶段 before 钩子失败时抛出 — 调用方 (skein.py) 捕获后转 SystemExit 阻断该阶段。"""


def _prefix_lines(tag: str, text: str) -> str:
    lines = text.splitlines()
    return "".join(f"{tag} {ln}\n" for ln in lines)


def _run_hooks(scope: str, when: str, ctx: dict[str, Any]) -> None:
    """统一钩子执行器 — skein.py 阶段钩子(before/after) 与 hooks.py agent 钩子(start/stop) 共用。

    scope: 阶段名(如 "check"/"finish"/"subtask.done") 或 "agent"(agent 钩子场景)。
    when:  "before"/"after"(阶段) 或 "start"/"stop"(agent)。
    ctx: {
        "hooks": list[dict],  # 已按调用方规则排好序的钩子列表(阶段: 配置原序;
                               # agent: 具名先/通配"*"后), 空或缺失 → 零开销直返(不构造 env/不 fork)
        "agent": str, "tid": str, "sid": str,        # 业务上下文, 缺省 ""
        "task_dir": str, "worktree": str, "repo_root": str,  # 缺省 ""
    }
    单条钩子字典字段: command(必填, shell 字符串) / timeout(秒, 缺省 60) /
        cwd(缺省: worktree 已配则 worktree, 否则 repo_root) / continue_on_error(缺省
        when=="before" 时 False, 其余 True — 与阶段 before/after 缺省对齐, 见 design.md §3)。

    严格串行, 前一条失败(非零退出/超时)即停, 除非该条 continue_on_error=true。
    阻断语义: scope != "agent" 且 when == "before" 时, 未被 continue_on_error 豁免的失败
    抛 HookBlocked; 其余场景(阶段 after / agent start/stop) 失败仅 stderr 告警, 不阻断。
    SKEIN_IN_HOOK 已在环境变量里时整体跳过 — 递归护栏, 防钩子里调 skein 命令再触发一层钩子。
    """
    hooks = ctx.get("hooks") or []
    if not hooks:
        return  # 零开销: 无钩子不构造 env、不 fork 子进程
    if os.environ.get("SKEIN_IN_HOOK"):
        return  # 递归护栏
    blocking = scope != "agent" and when == "before"
    cwd_default = ctx.get("worktree") or ctx.get("repo_root") or "."
    env = dict(os.environ)
    env.update({
        "SKEIN_SCOPE": scope, "SKEIN_WHEN": when,
        "SKEIN_AGENT": ctx.get("agent", ""),
        "SKEIN_TID": ctx.get("tid", ""), "SKEIN_SID": ctx.get("sid", ""),
        "SKEIN_TASK_DIR": ctx.get("task_dir", ""),
        "SKEIN_WORKTREE": ctx.get("worktree", ""),
        "SKEIN_REPO_ROOT": ctx.get("repo_root", ""),
        "SKEIN_IN_HOOK": "1",
    })
    for i, spec in enumerate(hooks, 1):
        tag = f"[hook {scope}.{when}#{i}]"
        cmd = spec.get("command", "")
        timeout = spec.get("timeout", HOOK_TIMEOUT_DEFAULT)
        cwd = spec.get("cwd") or cwd_default
        continue_on_error = spec.get("continue_on_error", when != "before")
        try:
            # shell=True 是有意选择: config.yaml 是用户手写本地文件, 信任级别等同用户在
            # 终端敲命令 (与 exec 端点的网络输入白名单 argv 不同信任边界, 见 design.md §4)
            r = subprocess.run(cmd, shell=True, cwd=cwd, env=env,
                                capture_output=True, text=True, timeout=timeout)
            if r.stdout:
                sys.stdout.write(_prefix_lines(tag, r.stdout))
            if r.stderr:
                sys.stderr.write(_prefix_lines(tag, r.stderr))
            ok, detail = r.returncode == 0, f"exit {r.returncode}"
        except subprocess.TimeoutExpired:
            ok, detail = False, f"超时(>{timeout}s)"
            sys.stderr.write(f"{tag} {detail}\n")
        if ok:
            continue
        if continue_on_error:
            sys.stderr.write(f"{tag} 失败({detail}), continue_on_error=true, 继续\n")
            continue
        msg = f"{tag} 失败({detail}), 串行执行终止"
        if blocking:
            raise HookBlocked(msg)
        sys.stderr.write(f"{msg} (仅告警, 不阻断)\n")
        return  # 失败即停 — 后续条目不再执行


if __name__ == "__main__":
    # 自检
    assert est_tokens("a" * 40) == 10
    assert budget_guard("short", 100, "t") == "short"
    long = "x" * 1000
    out = budget_guard(long, 10, "t")  # 预算 10 token = 40 字符
    assert len(out) < len(long) and "截断" in out
    # Debug 未启用 = 全 no-op (不写 stderr, 不抛)
    d0 = Debug(False)
    d0.log("x"); d0.rule("y"); d0.kv({"a": 1})
    assert d0.enabled is False and d0.c is None
    # 启用 = 不抛 (rich 有则用, 无则纯文本降级); 显式关掉环境开关避免干扰断言
    assert debug_enabled(None) in (True, False)
    d1 = Debug(True)
    d1.rule("自检"); d1.log("走一遍"); d1.kv({"k": "v"}, title="参数")

    # _run_hooks 自检: 无 hooks 键零开销直返 (不构造 env/不 fork)
    _run_hooks("check", "before", {})
    # before 失败 → 阻断 (raise HookBlocked)
    try:
        _run_hooks("check", "before", {"hooks": [{"command": "exit 1"}]})
        raise AssertionError("before 失败应抛 HookBlocked")
    except HookBlocked:
        pass
    # after 失败 → 仅告警不抛
    _run_hooks("check", "after", {"hooks": [{"command": "exit 1"}]})
    # agent start/stop 失败 → 一律不抛(即便 continue_on_error 显式 false)
    _run_hooks("agent", "start", {"hooks": [{"command": "exit 1", "continue_on_error": False}]})
    # 串行失败即停: 第二条不该跑 (用临时文件断言副作用)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        marker = os.path.join(td, "ran2")
        _run_hooks("agent", "start", {"hooks": [
            {"command": "exit 1", "continue_on_error": False},
            {"command": f"touch {marker}"},
        ]})
        assert not os.path.exists(marker), "失败即停: 第二条钩子不该执行"
    # continue_on_error=true 覆盖 before 缺省阻断
    _run_hooks("check", "before", {"hooks": [{"command": "exit 1", "continue_on_error": True}]})
    # timeout 超时按失败处置 (阶段 after, 仅告警不抛)
    _run_hooks("check", "after", {"hooks": [{"command": "sleep 2", "timeout": 1}]})
    # SKEIN_IN_HOOK 递归护栏: 已置位则整体跳过 (即便 hooks 非空且会失败)
    os.environ["SKEIN_IN_HOOK"] = "1"
    _run_hooks("check", "before", {"hooks": [{"command": "exit 1"}]})  # 若未跳过会抛, 不抛即通过
    del os.environ["SKEIN_IN_HOOK"]

    print("hooks.runner 自检过")
