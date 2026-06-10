#!/usr/bin/env bash
# TaskCompleted hook (command type)
# stdin: JSON {task_subject, task_id, cwd, ...}
# 职责: task 标记完成时, 校验是否有残留 worktree 未合并+移除。
#       有残留 → exit 2 (不标记完成 + stderr 反馈给 AI 要求先清理)。
# 退出码: 0 放行 / 2 打回 (残留 worktree)。

set -u

INPUT=$(cat 2>/dev/null || true)

TRELLISX_INPUT="$INPUT" python3 <<'PYEOF'
import json, os, sys, subprocess
raw = os.environ.get("TRELLISX_INPUT", "")
try:
    d = json.loads(raw)
except Exception:
    sys.exit(0)
cwd = d.get("cwd") or os.getcwd()
if not os.path.isdir(os.path.join(cwd, ".trellis")):
    sys.exit(0)

# 列 worktree, 检主仓库外的额外 worktree (排除主工作树)
try:
    out = subprocess.run(["git", "-C", cwd, "worktree", "list", "--porcelain"],
                         capture_output=True, text=True, timeout=5)
except Exception:
    sys.exit(0)  # git 不可用 → 放行
if out.returncode != 0:
    sys.exit(0)

# porcelain: 每个 worktree 一个 "worktree <path>" 块; 第一个是主工作树
paths = [l.split(" ", 1)[1] for l in out.stdout.splitlines() if l.startswith("worktree ")]
extra = paths[1:]  # 排除主工作树
if not extra:
    sys.exit(0)  # 无残留 → 放行

subj = d.get("task_subject") or d.get("task_id") or "<task>"
sys.stderr.write(
    f"trellisx: task '{subj}' 标记完成前检测到 {len(extra)} 个残留 worktree 未清理:\n"
    + "\n".join(f"  - {p}" for p in extra)
    + "\n\n完成前必须: 评估各 worktree diff → 合并到当前分支 (或丢弃) → "
      "git worktree remove <path> 移除。残留 worktree = 环境污染, 禁宣告完成。"
      "确认全部清理后重新标记完成。\n"
)
sys.exit(2)
PYEOF
