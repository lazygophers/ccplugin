#!/usr/bin/env bash
# SubagentStop hook (command type)
# stdin: JSON {cwd, stop_hook_active, ...}
# 职责: worktree 隔离的 sub-agent 完成时, 提醒 main 合并 + 清理 worktree。
# 输出: additionalContext 提醒 (不 block); 退出码 0。

set -u

PROMPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/prompts"
REINJECT_FILE="$PROMPTS_DIR/subagent-stop.md"

INPUT=$(cat 2>/dev/null || true)

REINJECT_FILE="$REINJECT_FILE" TRELLISX_INPUT="$INPUT" python3 <<'PYEOF'
import json, os, sys, subprocess
raw = os.environ.get("TRELLISX_INPUT", "")
try:
    d = json.loads(raw)
except Exception:
    sys.exit(0)
# 防循环
if d.get("stop_hook_active") is True:
    sys.exit(0)
cwd = d.get("cwd") or os.getcwd()
if not os.path.isdir(os.path.join(cwd, ".trellis")):
    sys.exit(0)

# 仅当存在额外 worktree 时才提醒 (sub-agent 可能用了 isolation: worktree)
try:
    out = subprocess.run(["git", "-C", cwd, "worktree", "list", "--porcelain"],
                         capture_output=True, text=True, timeout=5)
    paths = [l for l in out.stdout.splitlines() if l.startswith("worktree ")]
    if len(paths) <= 1:
        sys.exit(0)  # 无额外 worktree → 不提醒
except Exception:
    sys.exit(0)

try:
    with open(os.environ.get("REINJECT_FILE",""), encoding="utf-8") as f:
        ctx = f.read().strip()
except Exception:
    ctx = "trellisx: sub-agent 完成。若使用 isolation: worktree, main 必须 review worktree diff → 合并到当前分支 → git worktree remove 清理。"
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SubagentStop", "additionalContext": ctx}}, ensure_ascii=False))
PYEOF
