from __future__ import annotations

import json
import re
from typing import Any

ISSUE_URL = "https://github.com/lazygophers/ccplugin/issues/new"
OURS = ("skein.py", "spec.py", "CLAUDE_PLUGIN_ROOT")
BIN_RE = re.compile(r"(?:^|[\s;&|(])(?:skein-spec|skein)(?:\s|$)")
TRACEBACK_MARK = "Traceback (most recent call last)"


def cmd_report(payload: dict[str, Any]) -> int:
    command = payload.get("tool_input", {}).get("command", "")
    if not (any(marker in command for marker in OURS) or BIN_RE.search(command)):
        return 0
    error = (payload.get("tool_error", "") or "").strip()[:800]
    output: dict[str, Any] = {}
    if TRACEBACK_MARK in error:
        output["hookSpecificOutput"] = {"hookEventName": "PostToolUseFailure", "additionalContext": (
            f"SKEIN 脚本崩溃 (未捕获异常):\n命令: {command[:200]}\n错误: {error}\n"
            "这不是参数问题 — 引擎的门拒绝只出一行人话, 出 traceback 说明有异常没接住。")}
        output["systemMessage"] = (
            f"⚠️ SKEIN 脚本崩溃 (traceback), 疑似插件 bug 请手动开 issue: {ISSUE_URL} "
            "(附命令+错误+复现步骤)")
    else:
        output["hookSpecificOutput"] = {"hookEventName": "PostToolUseFailure", "additionalContext": (
            f"SKEIN 命令被拒 (非崩溃, 属正常校验):\n命令: {command[:200]}\n错误: {error}\n"
            "照错误提示改参数/补前置状态即可 — 这是引擎的门在起作用, 不是 bug。")}
    print(json.dumps(output))
    return 0


_TRACEBACK_MARK = TRACEBACK_MARK

__all__ = ["BIN_RE", "ISSUE_URL", "OURS", "TRACEBACK_MARK", "_TRACEBACK_MARK", "cmd_report"]
