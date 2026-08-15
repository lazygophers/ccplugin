from __future__ import annotations

import os
import sys

from skeinlib.hooks.runner import _run_hooks
from skeinlib.hooks.util import git_root


def cmd_agent_hook(when: str) -> int:
    argv = sys.argv[2:]
    options = {argv[index][2:]: argv[index + 1] for index in range(0, len(argv) - 1, 2) if argv[index].startswith("--")}
    agent = options.get("agent", "")
    task_id = options.get("tid", "")
    subtask_id = options.get("sid", "")
    root = git_root(options.get("cwd") or os.getcwd())
    import yaml
    try:
        config_path = os.path.join(root, ".skein", "config.yaml")
        if not os.path.exists(config_path):
            return 0
        with open(config_path, encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except (OSError, ValueError, yaml.YAMLError):
        return 0
    hooks = config.get("hooks") if isinstance(config, dict) else None
    agents = hooks.get("agent") if isinstance(hooks, dict) else None
    if not isinstance(agents, dict):
        return 0
    commands = [command for key in (agent, "*")
                if isinstance(agents.get(key), dict)
                for command in (agents[key].get(when) or [])]
    if not commands:
        return 0
    _run_hooks("agent", when, {"hooks": commands, "agent": agent, "tid": task_id, "sid": subtask_id, "repo_root": root})
    try:
        from skeinlib.spec.facade import Spec
        Spec()._write_audit("agent-hook", f"agent.{agent}", when, f"{len(commands)} hooks", f"tid={task_id} sid={subtask_id}")
    except (OSError, ValueError):
        pass
    return 0


__all__ = ["cmd_agent_hook"]
