#!/usr/bin/env bash
# PermissionRequest hook (command type)
# stdin: JSON {tool_name, tool_input, cwd, ...}
# 职责: trellis 项目内写盘工具弹权限时, allow + 注入提醒确认在 worktree 内操作。
#       不 deny (避免打断), 仅 additionalContext 提示。
# 输出: behavior allow + additionalContext; 退出码 0。

set -u

PROMPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/prompts"
REINJECT_FILE="$PROMPTS_DIR/permission-request.md"

INPUT=$(cat 2>/dev/null || true)

REINJECT_FILE="$REINJECT_FILE" TRELLISX_INPUT="$INPUT" python3 <<'PYEOF'
import json, os, sys
raw = os.environ.get("TRELLISX_INPUT", "")
try:
    d = json.loads(raw)
except Exception:
    sys.exit(0)
cwd = d.get("cwd") or os.getcwd()
if not os.path.isdir(os.path.join(cwd, ".trellis")):
    sys.exit(0)
# 仅写盘工具
tool = d.get("tool_name", "")
if tool not in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
    sys.exit(0)
try:
    with open(os.environ.get("REINJECT_FILE",""), encoding="utf-8") as f:
        ctx = f.read().strip()
except Exception:
    ctx = "trellisx: 写盘前确认 — 若属某 trellis task, 改动应落在该 task 的 worktree 内, 而非主工作区。"
# behavior allow (不改默认权限决策, 仅附提醒); 不带 updatedInput
print(json.dumps({
    "hookSpecificOutput": {"hookEventName": "PermissionRequest", "additionalContext": ctx}
}, ensure_ascii=False))
PYEOF
