#!/usr/bin/env bash
# SKEIN SessionStart hook — 把 core 规则常驻注入上下文。
# core 层设计为「每 session 必加载」, 故直接注入正文 (非仅指针); recall 层按需, 不在此注入。
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[ -z "$ROOT" ] && exit 0
[ -d "$ROOT/.claude/rules/core" ] || exit 0
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$DIR/../scripts/memory.py" inject-core 2>/dev/null | python3 -c '
import json, sys
body = sys.stdin.read().strip()
if not body:
    sys.exit(0)
ctx = "# SKEIN 常驻规则 (core)\n\n" + body
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
'
