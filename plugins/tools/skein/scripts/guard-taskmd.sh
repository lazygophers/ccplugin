#!/usr/bin/env bash
# SKEIN PreToolUse guard: 硬阻直接 Edit/Write/MultiEdit .skein/task.md。
# 看板必经 `skein.py board` 渲染 — 直接编辑会格式漂移 + 绕过 AI/脚本分工。
# 读 stdin hook payload, 命中则 exit 2 (block) 并把提示写 stderr。
set -euo pipefail
payload="$(cat)"
fp="$(printf '%s' "$payload" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("tool_input",{}).get("file_path",""))' 2>/dev/null || true)"
case "$fp" in
  */.skein/task.md)
    echo "🛑 禁直接编辑 .skein/task.md — 看板经 \`skein.py board\` 渲染。改 task 状态用 skein.py create/start/finish。" >&2
    exit 2
    ;;
esac
exit 0
