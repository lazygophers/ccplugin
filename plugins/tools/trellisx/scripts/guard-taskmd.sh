#!/usr/bin/env bash
# ponytail: PreToolUse guard — block direct Edit/Write of .trellis/task.md
# Reads stdin JSON (tool_name + tool_input.file_path). exit 2 = block (stderr shown to model).
# Why a hook when settings.json deny already blocks: deny is tool-level and project-root scoped;
# this hook also catches nested/absolute paths and gives an actionable hint.
set -euo pipefail

case "${1:-}" in
    -h|--help)
        echo "guard-taskmd.sh — PreToolUse hook (读 stdin JSON), 拦截直接编辑 .trellis/task.md; 无需手动调用"
        exit 0
        ;;
esac

payload="$(cat)"

tool_name="$(printf '%s' "$payload" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("tool_name",""))' 2>/dev/null || echo "")"
file_path="$(printf '%s' "$payload" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("tool_input",{}).get("file_path",""))' 2>/dev/null || echo "")"

case "$tool_name" in
    Edit|Write|MultiEdit)
        ;;
    *)
        exit 0
        ;;
esac

if [[ "$file_path" == *.trellis/task.md || "$file_path" == *"/.trellis/task.md" ]]; then
    echo "🔴 task.md 禁直接编辑, 经 .trellis/scripts/trellisx-taskmd.py 操作 (settings.json deny + 本 hook 双保险)" >&2
    exit 2
fi

exit 0
