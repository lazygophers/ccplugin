#!/usr/bin/env bash
# TaskCreated hook (command type)
# stdin: JSON {task_subject, task_id, cwd, ...}
# 职责: trellis task 创建时, 提醒为该 task 创建 worktree (不 block)。
# 输出: additionalContext 提醒; 退出码 0 (放行, 不阻止创建)。

set -u

PROMPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/prompts"
REINJECT_FILE="$PROMPTS_DIR/task-created.md"

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
try:
    with open(os.environ.get("REINJECT_FILE",""), encoding="utf-8") as f:
        ctx = f.read().strip()
except Exception:
    ctx = "trellisx: task 已创建。task.py start 后立即为该 task 创建独立 worktree (git worktree add), 全程隔离, 结束合并 + 移除。"
print(json.dumps({"hookSpecificOutput": {"hookEventName": "TaskCreated", "additionalContext": ctx}}, ensure_ascii=False))
PYEOF
