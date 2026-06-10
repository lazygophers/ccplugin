#!/usr/bin/env bash
# SessionEnd hook (command type)
# stdin: JSON {reason, cwd, ...}
# 职责: 会话结束时, 检测残留 worktree 记录到日志 (无 decision, 不能 block)。
# 默认 1.5s 超时 — 保持轻量。
# 退出码: 0 永远。

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
try:
    out = subprocess.run(["git", "-C", cwd, "worktree", "list", "--porcelain"],
                         capture_output=True, text=True, timeout=1)
    paths = [l.split(" ",1)[1] for l in out.stdout.splitlines() if l.startswith("worktree ")]
    extra = paths[1:]
    if extra:
        log = "/tmp/trellisx-orphan-worktrees.log"
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"[session-end] reason={d.get('reason','?')} cwd={cwd} orphans={extra}\n")
except Exception:
    pass
sys.exit(0)
PYEOF
