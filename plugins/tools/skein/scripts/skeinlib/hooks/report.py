"""report hook —— 本插件脚本失败时注入错误上下文 (原 report-skein.py)。

阻断语义: 本 hook 不阻断, 一律返回 0 —— 只在 additionalContext 里递错误信息。
"""
from __future__ import annotations

import json
import re
from typing import Any

ISSUE_URL = "https://github.com/lazygophers/ccplugin/issues/new"
OURS = ("skein.py", "spec.py", "CLAUDE_PLUGIN_ROOT")
# bin 短命令: 作为命令词出现 (行首或分隔符后), 避免 `.skein/` 之类路径误匹配
BIN_RE = re.compile(r"(?:^|[\s;&|(])(?:skein-spec|skein)(?:\s|$)")

# 「非零退出」有两种, 待遇必须不同:
#   ① 门拒绝 —— `confirm` 少 --approved、`start` 前置未完成、task 不存在……
#      引擎主动 `raise SkeinError`, 入口转成 `SystemExit(str(e))`, stderr 只有一行人话。
#      **这是功能正常工作**, 报「疑似插件 bug 请开 issue」纯属噪声, 还会教坏调用方
#      (每撞一次门就想去提 issue, 而不是照错误提示补参数)。
#   ② 真崩 —— 未捕获异常, stderr 带 `Traceback (most recent call last):`。这个才值得报。
# 判据就用 traceback 标记本身: 引擎的错误路径从不打印 traceback, 打印了就是没接住。
_TRACEBACK_MARK = "Traceback (most recent call last)"


def cmd_report(d: dict[str, Any]) -> int:
    """本插件脚本失败时注入错误上下文; **仅真崩溃 (带 traceback) 才引导开 issue**。"""
    cmd = d.get("tool_input", {}).get("command", "")
    if not (any(k in cmd for k in OURS) or BIN_RE.search(cmd)):
        return 0
    err = (d.get("tool_error", "") or "").strip()[:800]  # 截断防上下文膨胀
    crashed = _TRACEBACK_MARK in err
    out: dict[str, Any] = {}
    if crashed:
        out["hookSpecificOutput"] = {"hookEventName": "PostToolUseFailure", "additionalContext": (
            f"SKEIN 脚本崩溃 (未捕获异常):\n命令: {cmd[:200]}\n错误: {err}\n"
            "这不是参数问题 — 引擎的门拒绝只出一行人话, 出 traceback 说明有异常没接住。")}
        out["systemMessage"] = (
            f"⚠️ SKEIN 脚本崩溃 (traceback), 疑似插件 bug 请手动开 issue: {ISSUE_URL} "
            "(附命令+错误+复现步骤)")
    else:
        # 门拒绝: 只把错误原文递给调用方, 让它照提示改参数。不提 issue。
        out["hookSpecificOutput"] = {"hookEventName": "PostToolUseFailure", "additionalContext": (
            f"SKEIN 命令被拒 (非崩溃, 属正常校验):\n命令: {cmd[:200]}\n错误: {err}\n"
            "照错误提示改参数/补前置状态即可 — 这是引擎的门在起作用, 不是 bug。")}
    print(json.dumps(out))
    return 0
