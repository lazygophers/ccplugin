#!/usr/bin/env python3
"""SKEIN PostToolUseFailure hook: 本插件脚本报错时注入上下文 + 引导手动报 issue。

仅当失败的是本插件自有脚本 (命令含 skein.py / memory.py / CLAUDE_PLUGIN_ROOT) 才触发,
把 tool_error 注入 additionalContext 供 model 诊断, 并 systemMessage 引导用户手动开 issue
(不自动建 issue — 避免误报刷屏)。其余工具失败一律静默 exit 0。
"""
import json
import sys

ISSUE_URL = "https://github.com/lazygophers/ccplugin/issues/new"
OURS = ("skein.py", "memory.py", "CLAUDE_PLUGIN_ROOT")


def main() -> int:
    try:
        d = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    cmd = d.get("tool_input", {}).get("command", "")
    if not any(k in cmd for k in OURS):
        return 0
    err = (d.get("tool_error", "") or "").strip()[:800]  # 截断防上下文膨胀
    ctx = (f"SKEIN 脚本执行失败:\n命令: {cmd[:200]}\n错误: {err}\n"
           "先自查 (工作区是否 init / 参数是否合法); 属插件 bug 则手动报 issue。")
    msg = f"⚠️ SKEIN 脚本报错, 疑似插件 bug 请手动开 issue: {ISSUE_URL} (附命令+错误+复现步骤)"
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUseFailure", "additionalContext": ctx},
        "systemMessage": msg}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
