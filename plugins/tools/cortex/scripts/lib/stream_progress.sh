#!/usr/bin/env bash
# cortex/scripts/lib/stream_progress.sh
#
# Stream-json progress visibility library for cortex wrappers.
#
# Three layers of feedback while `claude --bare -p` runs heavy tasks:
#   L1 — step progress markers ("[label] step 1/2: ...") on stderr
#   L2 — incremental jq parse of --output-format stream-json events on stderr
#   L3 — heartbeat every 10s ("[label] still working... (Xs elapsed)") on stderr
#
# Source-only library (no top-level side effects, idempotent to re-source).
# Usage:
#   source "$LIB_PATH"
#   export CORTEX_JOB_LABEL="cortex-doctor"        # optional, default "cortex"
#   export CORTEX_STREAM_TEE_FILE="/tmp/x.ndjson"  # optional, capture raw NDJSON
#   cortex_stream_runner claude --bare -p "..."    # auto-injects stream-json
#
# Contract:
#   - cortex_stream_runner appends `--output-format stream-json --verbose` once.
#   - If jq is unavailable, falls back to raw passthrough (claude still runs).
#   - Heartbeat process is killed via trap EXIT — covers normal exit, set -e,
#     and signal interrupts. No zombies.
#   - Stdout of cortex_stream_runner is empty in jq path; raw NDJSON only
#     lands in $CORTEX_STREAM_TEE_FILE when set, never on stdout.
#   - Return code is the claude exit code (PIPESTATUS[0] when piped through jq).

# Guard against double-source (idempotent).
if [[ -n "${_CORTEX_STREAM_PROGRESS_LOADED:-}" ]]; then
  return 0 2>/dev/null || true
fi
_CORTEX_STREAM_PROGRESS_LOADED=1

# Detect jq availability. Sets CORTEX_NO_JQ=1 on absence, returns non-zero.
cortex_check_jq() {
  if command -v jq >/dev/null 2>&1; then
    return 0
  fi
  CORTEX_NO_JQ=1
  return 1
}

# Background heartbeat. Emits one line every 10s on stderr.
# Arg 1: label string.
_cortex_heartbeat() {
  local start=$SECONDS
  local label="${1:-cortex}"
  while true; do
    sleep 10
    echo "[${label}] still working... ($((SECONDS - start))s elapsed)" >&2
  done
}

# jq filter (single-quoted; jq variables only).
# Extracts user-visible text from assistant messages, tool_use summaries,
# and final result status. Unknown event types are dropped (empty).
_CORTEX_JQ_FILTER='
  if .type == "assistant" then
    (.message.content // []) | .[] |
    if .type == "text" then
      "[text] \(.text | ltrimstr("\n") | .[0:200])"
    elif .type == "tool_use" then
      "[tool: \(.name)] \(.input | tostring | .[0:120])"
    else empty end
  elif .type == "result" then
    if .is_error then "[FAILED] \(.result // "unknown error")"
    else "[OK] done"
    end
  else empty end
'

# cortex_stream_runner CMD [ARGS...]
#
# Runs the given command with --output-format stream-json --verbose appended,
# parses the NDJSON stdout through jq into human-readable lines on stderr,
# and runs a heartbeat in the background.
#
# Optional env:
#   CORTEX_JOB_LABEL      — label prefix for log lines (default "cortex")
#   CORTEX_STREAM_TEE_FILE — if set, raw NDJSON is also tee'd to this path
#
# Exit code: child's exit code (claude / timeout wrapper).
cortex_stream_runner() {
  local label="${CORTEX_JOB_LABEL:-cortex}"
  local tee_file="${CORTEX_STREAM_TEE_FILE:-}"

  # jq absent → fail-soft: run command raw, preserve stdout for caller.
  if ! cortex_check_jq; then
    echo "[${label}] step 1/2: jq missing, running claude without live parse" >&2
    if [[ -n "$tee_file" ]]; then
      "$@" --output-format stream-json --verbose | tee "$tee_file" >/dev/null
      return ${PIPESTATUS[0]}
    fi
    "$@" --output-format stream-json --verbose
    return $?
  fi

  echo "[${label}] step 1/2: 启动 claude (stream-json 模式)" >&2

  # Heartbeat in background; trap EXIT on the current shell (function scope
  # cannot install function-local traps in bash 3.2, so install on the caller
  # shell and clear at the end). To stay isolated, use a subshell instead.
  local rc=0
  (
    _cortex_heartbeat "$label" &
    local hb_pid=$!
    # shellcheck disable=SC2064
    trap "kill $hb_pid 2>/dev/null; wait $hb_pid 2>/dev/null" EXIT INT TERM

    echo "[${label}] step 2/2: 等待 claude 输出..." >&2

    if [[ -n "$tee_file" ]]; then
      "$@" --output-format stream-json --verbose 2> >(cat >&2) \
        | tee "$tee_file" \
        | jq -r --unbuffered "$_CORTEX_JQ_FILTER" >&2
      rc=${PIPESTATUS[0]}
    else
      "$@" --output-format stream-json --verbose 2> >(cat >&2) \
        | jq -r --unbuffered "$_CORTEX_JQ_FILTER" >&2
      rc=${PIPESTATUS[0]}
    fi

    exit $rc
  )
  rc=$?

  if [[ $rc -eq 0 ]]; then
    echo "[${label}] OK" >&2
  else
    echo "[${label}] FAILED: exit code $rc" >&2
  fi
  return $rc
}
