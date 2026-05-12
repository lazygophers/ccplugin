#!/usr/bin/env bash
# post_compact.sh
# CC PostCompact hook — 把 compact 摘要落到 记忆/L4-流水账/ledger/YYYY-MM/DD-HHMM-compact.md。
#
# 与 stop.sh 共享 save_session.py 实现, reason=compact。
# compact 总是落档 (跳过启发式判定 — compact summary 本身已是浓缩信息)。
# 协议同 stop.sh: 永远 exit 0, 命中输出 v2 wrapped JSON。

set -u

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex"
LOG_FILE="${HOME}/.cache/cortex/post_compact.log"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

log() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG_FILE" 2>/dev/null || true; }

HOOK_INPUT=$(cat 2>/dev/null || true)
if [[ -z "$HOOK_INPUT" ]]; then
  log "post_compact: empty stdin"
  exit 0
fi

read -r TRANSCRIPT_PATH SESSION_ID < <(printf '%s' "$HOOK_INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    if not isinstance(d, dict):
        d = {}
except Exception:
    d = {}
print(d.get('transcript_path', '') or '-', d.get('session_id', '') or '-')
" 2>>"$LOG_FILE") || { log "post_compact: parse failed"; exit 0; }

[[ "$TRANSCRIPT_PATH" == "-" ]] && TRANSCRIPT_PATH=""
[[ "$SESSION_ID" == "-" ]] && SESSION_ID=""

# shellcheck source=./_lib/resolve_vault.sh
source "$PLUGIN_ROOT/hooks/_lib/resolve_vault.sh"
VAULT=$(resolve_vault 2>/dev/null || true)
if [[ -z "$VAULT" ]]; then
  log "post_compact: vault not resolved; skip"
  exit 0
fi

if [[ -z "$TRANSCRIPT_PATH" || ! -f "$TRANSCRIPT_PATH" ]]; then
  log "post_compact: transcript missing ($TRANSCRIPT_PATH)"
  exit 0
fi

SAVE_OUT=$(python3 "$PLUGIN_ROOT/hooks/_lib/save_session.py" \
  --vault "$VAULT" \
  --transcript "$TRANSCRIPT_PATH" \
  --reason compact \
  --cli claude-code \
  --cli-session "$SESSION_ID" \
  --force \
  2>>"$LOG_FILE")
SAVE_RC=$?

if [[ "$SAVE_RC" == "0" && -n "$SAVE_OUT" ]]; then
  log "compact saved: $SAVE_OUT"
  REL=$(python3 -c "
import os, sys
try: print(os.path.relpath(sys.argv[2], sys.argv[1]))
except Exception: print(sys.argv[2])
" "$VAULT" "$SAVE_OUT" 2>/dev/null || echo "$SAVE_OUT")
  python3 -c "
import json, sys
sys.stdout.write(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PostCompact',
        'additionalContext': f'📝 cortex 已落档 compact 摘要: {sys.argv[1]}',
    }
}, ensure_ascii=False))
" "$REL" 2>>"$LOG_FILE" || true
else
  log "compact save rc=$SAVE_RC"
fi

exit 0
