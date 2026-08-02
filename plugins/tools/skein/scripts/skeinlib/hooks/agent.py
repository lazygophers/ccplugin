"""agent 生命周期钩子 (`agent-start` / `agent-stop`) —— 与其余子命令**协议不同**。

其余子命令走 harness 的 stdin JSON 协议; 这两个是用户/agent 显式调用的, 参数走 `--flag value`
argv。分开一个模块就是为了让这个差别显眼 —— 混在 stdin 那堆里, 迟早有人给它加读 stdin 的逻辑,
然后在没有输入的时候空等。

阻断语义与阶段钩子相反: 阶段钩子的 before 可以阻断, agent 钩子**永不返回非零** —— 钩子挂了
不该让 subtask 跟着算失败 (design.md §3)。
"""
from __future__ import annotations

import os
import sys

import yaml  # type: ignore[import-untyped]

from skeinlib.hooks.util import git_root


def cmd_agent_hook(when: str) -> int:
    """查 hooks.agent.<name>.<when> (+ "*"), 无配置即 no-op; 命中则经 runner._run_hooks 执行
    (具名先跑, "*" 后跑)。"""
    argv = sys.argv[2:]
    opts: dict[str, str] = {}
    for i in range(0, len(argv) - 1, 2):
        if argv[i].startswith("--"):
            opts[argv[i][2:]] = argv[i + 1]
    agent = opts.get("agent", "")
    tid = opts.get("tid", "")
    sid = opts.get("sid", "")
    root = git_root(opts.get("cwd") or os.getcwd())
    try:
        cfg_path = os.path.join(root, ".skein", "config.yaml")
        if not os.path.exists(cfg_path):
            return 0
        with open(cfg_path, encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh)
    except (OSError, ValueError, yaml.YAMLError):
        return 0  # 未初始化 / 配置语法错 → 静默放行 (钩子永不阻断 agent)
    spec = cfg.get("hooks")
    if not isinstance(spec, dict):
        return 0  # 无 hooks 键: 零开销直返, 不解析深层不 fork
    agents = spec.get("agent")
    if not isinstance(agents, dict):
        return 0
    # 具名先, 通配 "*" 后 (具体优先于通配)
    todo = [c for key in (agent, "*")
            if isinstance(agents.get(key), dict)
            for c in (agents[key].get(when) or [])]
    if not todo:
        return 0
    from skeinlib.hooks.runner import _run_hooks  # lazy: 仅命中时才 fork 子进程
    _run_hooks("agent", when, {"hooks": todo, "agent": agent, "tid": tid, "sid": sid, "repo_root": root})
    try:  # 审计: 供 doctor 检查「配了 agent 钩子但从未触发」; 写失败不影响钩子已执行的事实
        from skeinlib.spec.facade import Spec
        Spec()._write_audit("agent-hook", f"agent.{agent}", when, f"{len(todo)} hooks", f"tid={tid} sid={sid}")
    except (OSError, ValueError):
        pass
    return 0
