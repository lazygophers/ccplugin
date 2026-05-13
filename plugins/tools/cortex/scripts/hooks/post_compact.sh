#!/usr/bin/env bash
# post_compact.sh — CC PostCompact hook
#
# 行为: 同 stop.sh, 把 compact 后的 transcript jsonl 完整 copy 到
#   vault/记忆/L4-流水账/sessions/<cli>/<YYYY>/<MM>/<DD>/<session_id>-compact.jsonl
# (与 Stop 副本同目录, suffix -compact 区分)
#
# 协议同 stop.sh. 永远 exit 0.

set -u

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex}"
LOG_FILE="${HOME}/.cache/cortex/post_compact.log"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

log() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG_FILE" 2>/dev/null || true; }

HOOK_INPUT=$(cat 2>/dev/null || true)
if [[ -z "$HOOK_INPUT" ]]; then
  log "post_compact: empty stdin"
  exit 0
fi

_PARSED=$(printf '%s' "$HOOK_INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    if not isinstance(d, dict):
        d = {}
except Exception:
    d = {}
print(
    d.get('transcript_path', '') or '-',
    d.get('hook_event_name', '') or 'PostCompact',
    d.get('session_id', '') or '-',
)
" 2>>"$LOG_FILE") || { log "post_compact: parse failed"; exit 0; }
read -r TRANSCRIPT_PATH HOOK_EVENT SESSION_ID <<< "$_PARSED"

[[ "$TRANSCRIPT_PATH" == "-" ]] && TRANSCRIPT_PATH=""
[[ "$SESSION_ID" == "-" ]] && SESSION_ID=""

if [[ -z "$TRANSCRIPT_PATH" ]] || [[ ! -f "$TRANSCRIPT_PATH" ]]; then
  log "post_compact: transcript missing"
  exit 0
fi

# shellcheck source=./_lib/resolve_vault.sh
source "$PLUGIN_ROOT/scripts/hooks/_lib/resolve_vault.sh"
VAULT=$(resolve_vault)
if [[ -z "$VAULT" ]]; then
  log "post_compact: vault not resolved"
  exit 0
fi

CLI="claude-code"
YYYY=$(date '+%Y')
MM=$(date '+%m')
DD=$(date '+%d')
ID="${SESSION_ID:-$(basename "$TRANSCRIPT_PATH" .jsonl)}-compact"
DEST_DIR="$VAULT/记忆/L4-流水账/sessions/$CLI/$YYYY/$MM/$DD"
DEST="$DEST_DIR/${ID}.jsonl"

mkdir -p "$DEST_DIR" 2>/dev/null || { log "post_compact: mkdir failed"; exit 0; }

if cp "$TRANSCRIPT_PATH" "$DEST" 2>>"$LOG_FILE"; then
  REL="${DEST#$VAULT/}"
  log "post_compact: copied → $REL"
  python3 -c "
import json, sys
payload = {
    'hookSpecificOutput': {
        'hookEventName': sys.argv[1],
        'additionalContext': f'📝 cortex 已落档 {sys.argv[2]}',
    }
}
sys.stdout.write(json.dumps(payload, ensure_ascii=False))
" "$HOOK_EVENT" "$REL" 2>>"$LOG_FILE" || true
else
  log "post_compact: cp failed"
fi

exit 0
