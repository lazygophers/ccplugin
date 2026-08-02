"""UserPromptSubmit —— **全仓最热的一段代码**, 每一句用户输入都跑一遍。

它决定注入什么: 未初始化 → setup 硬提示; 已初始化 → 单一 `_CTX` (判据 + 本次命中的信号证据
+ 回复前缀规则 + 当前 task 阶段 + 运行配置)。**档位不在这里判** —— 只给证据, 走 flow 还是
inline 交 AI 读 `_CTX` 里的判据自己定。

改这里前先读 `skeinlib/hooks/__init__.py` 的热路径纪律: 重 import 一律局部, 正则模块级预编译。
"""
from __future__ import annotations

import json
import os
from typing import Any

from skeinlib.hooks.judge import (_CTX, _PREFIX_RULE, _UNINIT_PLAIN, _UNINIT_TRELLIS,
                                  _judge_signal, _task_phase_hints)
from skeinlib.hooks.util import git_root

# 显式走 skein 流程的输入: 用户已经决定了, 无需路由启发, 也无需未初始化提示
_EXPLICIT = ("go", "exec", "do", "plan", "继续", "continue")
_EXPLICIT_PREFIX = ("/skein-", "/skein:skein-", "skein-")


def _run_config(dir_: str) -> tuple[bool, int, bool]:
    """读 config.yaml 的 worktree.enabled + pools.work + auto_commit (旧扁平键 deprecated fallback 仍生效);
    默认从 skeinlib.config.CONFIG_DEFAULTS (hook 不硬编码)。"""
    from skeinlib.config import CONFIG_DEFAULTS, Config  # lazy: 仅已初始化热路径需要; 默认真值唯一来源
    try:
        cfg = Config(os.path.join(dir_, "config.yaml")).effective()
    except (OSError, ValueError):
        cfg = CONFIG_DEFAULTS
    uw = bool(cfg["worktree"]["enabled"])
    ac = bool(cfg["auto_commit"])
    ma = cfg["pools"]["work"]
    env = os.environ.get("CLAUDE_PLUGIN_OPTION_MAX_ACTIVE")
    if env and env.strip().isdigit():
        ma = int(env)
    return uw, int(ma), ac


def cmd_user_prompt(d: dict[str, Any]) -> int:
    """UserPromptSubmit: 每 prompt 必注入。未初始化 → 硬提示先 setup; 已初始化 → 注入单一 _CTX (含命中信号证据, 走 flow/inline 交 AI 读判据自判)。"""
    prompt = (d.get("prompt", "") or "").strip()
    if prompt in _EXPLICIT or prompt.startswith(_EXPLICIT_PREFIX):
        return 0
    root = git_root(d.get("cwd") or os.getcwd())
    dir_ = os.path.join(root, ".skein")
    has_git = os.path.isdir(os.path.join(root, ".git"))
    # 非 git 且无 .skein: 别在任意目录 nag (用户 setup/init 建了 .skein 才接管)
    if not has_git and not os.path.isdir(dir_):
        return 0
    if not os.path.exists(os.path.join(dir_, "config.yaml")):
        ctx = _UNINIT_TRELLIS if os.path.isdir(os.path.join(root, ".trellis")) else _UNINIT_PLAIN
    else:
        evidence = _judge_signal(d.get("prompt", "") or "")
        ctx = _CTX
        if evidence:
            ctx += f"\n本次命中: {', '.join(evidence)}"
        ctx += "\n\n" + _PREFIX_RULE + _task_phase_hints(dir_)
        uw, ma, ac = _run_config(dir_)
        wt_txt = "启用 (task 各开 worktree 隔离)" if uw else "禁用 (原地执行, 无 worktree)"
        # worktree 模式下 finish 必 commit (不提交则 merge 丢改动), auto_commit 只对原地模式生效
        ac_txt = ("强制 (worktree 模式必自动 commit, 本配置不生效)" if uw
                  else ("启用 (finish 时自动 commit)" if ac else "禁用 (改动需手动 commit)"))
        ctx += f"\n\n# SKEIN 运行配置\n- worktree: {wt_txt}\n- 最大并行 subtask: {ma}\n- auto_commit: {ac_txt}"
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit", "additionalContext": ctx}}))
    return 0
