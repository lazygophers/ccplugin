#!/usr/bin/env bash
# stop.sh — CC Stop / SubagentStop hook
#
# 行为: 把会话 jsonl transcript 完整 copy 到
#   vault/记忆/L4-流水账/sessions/<cli>/<YYYY>/<MM>/<DD>/<session_id>.jsonl
#
# 协议:
# - stdin: CC hook v2 JSON (含 transcript_path, session_id, stop_hook_active, hook_event_name)
# - stdout: copy 成功时输出 v2 wrapped JSON (additionalContext = 落档路径); 否则空
# - 退出码: 永远 0 (advisory; 不阻断会话)
#
# 失败统一写 ~/.cache/cortex/stop.log, 不抛错给主线。

set -u

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex}"
LOG_FILE="${HOME}/.cache/cortex/stop.log"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

log() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG_FILE" 2>/dev/null || true; }

# ---- 读 stdin ----
HOOK_INPUT=$(cat 2>/dev/null || true)
if [[ -z "$HOOK_INPUT" ]]; then
  log "stop: empty stdin"
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
    'true' if d.get('stop_hook_active') else 'false',
    d.get('hook_event_name', '') or 'Stop',
    d.get('session_id', '') or '-',
)
" 2>>"$LOG_FILE") || { log "stop: parse failed"; exit 0; }
read -r TRANSCRIPT_PATH STOP_ACTIVE HOOK_EVENT SESSION_ID <<< "$_PARSED"

[[ "$TRANSCRIPT_PATH" == "-" ]] && TRANSCRIPT_PATH=""
[[ "$SESSION_ID" == "-" ]] && SESSION_ID=""

# 防循环
if [[ "$STOP_ACTIVE" == "true" ]]; then
  log "stop: stop_hook_active=true; skip"
  exit 0
fi

# transcript 必须存在
if [[ -z "$TRANSCRIPT_PATH" ]] || [[ ! -f "$TRANSCRIPT_PATH" ]]; then
  log "stop: transcript missing ($TRANSCRIPT_PATH)"
  exit 0
fi

# 解析 vault
# shellcheck source=./_lib/resolve_vault.sh
source "$PLUGIN_ROOT/scripts/hooks/_lib/resolve_vault.sh"
VAULT=$(resolve_vault)
if [[ -z "$VAULT" ]]; then
  log "stop: vault not resolved; silent exit"
  exit 0
fi

# 目标: vault/记忆/L4-流水账/sessions/<cli>/<YYYY>/<MM>/<DD>/<id>.jsonl
CLI="claude-code"
YYYY=$(date '+%Y')
MM=$(date '+%m')
DD=$(date '+%d')
ID="${SESSION_ID:-$(basename "$TRANSCRIPT_PATH" .jsonl)}"
DEST_DIR="$VAULT/记忆/L4-流水账/sessions/$CLI/$YYYY/$MM/$DD"
DEST="$DEST_DIR/${ID}.jsonl"

mkdir -p "$DEST_DIR" 2>/dev/null || { log "stop: mkdir failed: $DEST_DIR"; exit 0; }

if cp "$TRANSCRIPT_PATH" "$DEST" 2>>"$LOG_FILE"; then
  REL="${DEST#$VAULT/}"
  log "stop: copied → $REL (event=$HOOK_EVENT)"
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
  log "stop: cp failed"
fi

exit 0
