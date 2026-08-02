"""config.yaml 默认值 + 常量 + hooks 骨架 — 单一真值源。"""
from __future__ import annotations

from typing import Any

# config-hooks/c4: 阶段命令的合法阶段名 — hooks.<name> 的 <name> 唯一真值源, 校验/报错消息共用。
STAGE_NAMES = ("create", "confirm", "research", "plan", "exec", "check", "finishing", "finish", "archive",
               "subtask.start", "subtask.done", "subtask.fail")

# config.yaml 全部键的默认值 — init 写入 + config() 缺键自动回填的唯一真值源。
CONFIG_DEFAULTS: dict[str, Any] = {
    "auto_commit": True,
    "retain_days": 7,
    "pools": {
        "work": 2,
        "gate": 3,
    },
    "worktree": {
        "enabled": False,
        "root": ".worktrees",
    },
    "web": {
        "serve": True,
        "board_open": True,
    },
    "spec": {
        "core_budget": 400,
        "always_budget": 517,
    },
    "hooks": {
        "create": {"before": [], "after": []},
        "confirm": {"before": [], "after": []},
        "research": {"before": [], "after": []},
        "plan": {"before": [], "after": []},
        "exec": {"before": [], "after": []},
        "check": {"before": [], "after": []},
        "finishing": {"before": [], "after": []},
        "finish": {"before": [], "after": []},
        "archive": {"before": [], "after": []},
        "subtask.start": {"before": [], "after": []},
        "subtask.done": {"before": [], "after": []},
        "subtask.fail": {"before": [], "after": []},
        "agent": {"*": {"start": [], "stop": []}},
    },
}

# CONFIG_DEFAULTS 中禁止经 http 写端点修改的键 — 值会被当 shell 命令执行, 远程可写 = RCE。
CFG_REMOTE_DENY = ("hooks",)
# 不参与点号路径体系的键 (config set / 展示 / 路径校验一律跳过)。
CFG_NO_PATH = ("hooks",)

# hooks 结构骨架
HOOK_SCOPES = ("agent",) + STAGE_NAMES
HOOK_WHENS_STAGE = ("before", "after")
HOOK_WHENS_AGENT = ("start", "stop")
HOOK_ENTRY_TYPES = ("command",)
HOOK_ENTRY_FIELDS = ("type", "command", "timeout", "continue_on_error", "cwd")
HOOK_ENTRY_REQUIRED = ("command",)

# init 写进 config.yaml 尾部的注释骨架
HOOKS_SKELETON = """
# ── hooks (可选; 取消注释即用, 全量说明见 plugins/tools/skein/docs/hooks.md) ──
# 阶段钩子: <阶段>.before 失败会阻断该阶段; .after 失败只告警。
#   合法阶段: create confirm start check finish archive subtask.start subtask.done subtask.fail
# agent 钩子: <agent 名或 "*">.start / .stop, 失败一律只告警不阻断 subtask。
# 条目字段: type(必填, 目前仅 command) command(必填) timeout(秒, 缺省 60)
#           continue_on_error(true/false) cwd(缺省 = task 工作目录)
# 上下文经 env 注入: SKEIN_SCOPE SKEIN_WHEN SKEIN_AGENT SKEIN_TID SKEIN_SID
#                   SKEIN_TASK_DIR SKEIN_WORKTREE SKEIN_REPO_ROOT
# ⚠️ 钩子里禁调 skein 的写命令 (撞工作区写锁会等到超时); 只读命令如 skein list 可以。
#
# hooks:
#   check:
#     before:
#       - type: command
#         command: "npm run lint"
#         timeout: 120
#   finish:
#     after:
#       - type: command
#         command: "echo \\"$SKEIN_TID 已完成\\""
#   agent:
#     skein-executor:
#       stop:
#         - type: command
#           command: "npm run format"
#     "*":
#       start:
#         - type: command
#           command: "echo \\"$SKEIN_AGENT 开工\\""
"""

# 旧扁平键 → 新嵌套 (组, 叶) 路径映射
CFG_LEGACY: dict[str, tuple[str, str]] = {
    "use_worktree": ("worktree", "enabled"),
    "worktree_root": ("worktree", "root"),
    "web_serve": ("web", "serve"),
    "board_open": ("web", "board_open"),
    "spec_core_budget": ("spec", "core_budget"),
    "spec_always_budget": ("spec", "always_budget"),
}
