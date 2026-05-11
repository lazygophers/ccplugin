#!/usr/bin/env bash
# stop.sh
# CC Stop / SubagentStop hook — 启发式判定是否落档当前会话。
#
# 协议:
# - stdin: CC hook v2 JSON (含 transcript_path, session_id, cwd, stop_hook_active, hook_event_name)
# - stdout: 命中且写入成功时输出 v2 wrapped JSON (additionalContext = 一行简讯); 否则空
# - 退出码: 永远 0 (advisory; 不阻断会话)
#
# 失败统一写 ~/.cache/cortex/stop.log, 不抛错给主线。

set -u

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
LOG_FILE="${HOME}/.cache/cortex/stop.log"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

log() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG_FILE" 2>/dev/null || true; }

# ---- 读 stdin ----
HOOK_INPUT=$(cat 2>/dev/null || true)
if [[ -z "$HOOK_INPUT" ]]; then
  log "stop: empty stdin"
  exit 0
fi

# 解析 JSON 关键字段
read -r TRANSCRIPT_PATH STOP_ACTIVE HOOK_EVENT SESSION_ID < <(printf '%s' "$HOOK_INPUT" | python3 -c "
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

[[ "$TRANSCRIPT_PATH" == "-" ]] && TRANSCRIPT_PATH=""
[[ "$SESSION_ID" == "-" ]] && SESSION_ID=""

# 防循环
if [[ "$STOP_ACTIVE" == "true" ]]; then
  log "stop: stop_hook_active=true; skip"
  exit 0
fi

# 事件 → reason
case "$HOOK_EVENT" in
  SubagentStop) REASON="subagent-stop" ;;
  PostCompact)  REASON="compact" ;;
  Stop|*)       REASON="stop" ;;
esac

# ---- 解析 vault ----
# shellcheck source=./_lib/resolve_vault.sh
source "$PLUGIN_ROOT/hooks/_lib/resolve_vault.sh"
VAULT=$(resolve_vault 2>/dev/null || true)
if [[ -z "$VAULT" ]]; then
  log "stop: vault not resolved; skip ($HOOK_EVENT)"
  exit 0
fi

# transcript 不存在 → 仅日志, 不写 vault (除非是 manual force 调用, 此处不处理)
if [[ -z "$TRANSCRIPT_PATH" || ! -f "$TRANSCRIPT_PATH" ]]; then
  log "stop: transcript missing ($TRANSCRIPT_PATH) reason=$REASON; skip"
  exit 0
fi

# ---- 调度 save_session.py ----
SAVE_OUT=$(python3 "$PLUGIN_ROOT/hooks/_lib/save_session.py" \
  --vault "$VAULT" \
  --transcript "$TRANSCRIPT_PATH" \
  --reason "$REASON" \
  --cli claude-code \
  --cli-session "$SESSION_ID" \
  2>>"$LOG_FILE")
SAVE_RC=$?

case "$SAVE_RC" in
  0)
    log "saved: $SAVE_OUT (event=$HOOK_EVENT)"
    REL=$(python3 -c "
import os, sys
vault = sys.argv[1]; abs_p = sys.argv[2]
try:
    print(os.path.relpath(abs_p, vault))
except Exception:
    print(abs_p)
" "$VAULT" "$SAVE_OUT" 2>/dev/null || echo "$SAVE_OUT")
    # 输出 v2 wrapped JSON
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
    ;;
  2)
    log "skipped: heuristic threshold not met (event=$HOOK_EVENT)"
    ;;
  *)
    log "save failed rc=$SAVE_RC (event=$HOOK_EVENT)"
    ;;
esac

# ---- P5: vault auto-commit (opt-in) ----
# 异步隔离, 不阻塞 hook 返回; git_sync.py 内部 fail-soft.
if [[ -n "${VAULT:-}" ]]; then
  (
    CORTEX_VAULT_PATH="$VAULT" \
      python3 "$PLUGIN_ROOT/hooks/_lib/git_sync.py" auto "$VAULT" \
      >>"$LOG_FILE" 2>&1
  ) &
  disown 2>/dev/null || true
fi

exit 0
