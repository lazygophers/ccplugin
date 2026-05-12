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

# ANSI color palette (initialized once at source time).
# tty detection on stderr fd 2 — non-tty (cron / pipe / file) → empty strings.
# 8-color basic codes (30-37 / bold=1 / dim=2) for bash 3.2 + old terminal compat.
if [[ -t 2 ]]; then
  _C_RESET=$'\033[0m'
  _C_BOLD=$'\033[1m'
  _C_DIM=$'\033[2m'
  _C_CYAN=$'\033[36m'
  _C_GREEN=$'\033[32m'
  _C_YELLOW=$'\033[33m'
  _C_RED=$'\033[31m'
  _C_MAGENTA=$'\033[35m'
  # jq filter uses ANSI codes too (tty branch).
  _CORTEX_JQ_TTY=1
else
  _C_RESET=""
  _C_BOLD=""
  _C_DIM=""
  _C_CYAN=""
  _C_GREEN=""
  _C_YELLOW=""
  _C_RED=""
  _C_MAGENTA=""
  _CORTEX_JQ_TTY=0
fi

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
    echo "${_C_DIM}[${label}] still working... ($((SECONDS - start))s elapsed)${_C_RESET}" >&2
  done
}

# jq filter (single-quoted; jq variables only).
# Extracts user-visible text from assistant messages, tool_use summaries,
# and final result status. Unknown event types are dropped (empty).
#
# Two variants: tty (ANSI-colored, ESC = ) and plain (cron / log files).
# ANSI: text=green, tool=yellow, OK=bold-green, FAILED=bold-red.
if [[ "$_CORTEX_JQ_TTY" == "1" ]]; then
  _CORTEX_JQ_FILTER='
    def c_text:   "[32m";
    def c_tool:   "[33m";
    def c_ok:     "[32;1m";
    def c_fail:   "[31;1m";
    def c_reset:  "[0m";
    if .type == "assistant" then
      (.message.content // []) | .[] |
      if .type == "text" then
        c_text + "[text] " + (.text | ltrimstr("\n") | .[0:200]) + c_reset
      elif .type == "tool_use" then
        c_tool + "[tool: " + .name + "] " + (.input | tostring | .[0:120]) + c_reset
      else empty end
    elif .type == "result" then
      if .is_error then c_fail + "[FAILED] " + (.result // "unknown error") + c_reset
      else c_ok + "[OK] done" + c_reset
      end
    else empty end
  '
else
  _CORTEX_JQ_FILTER='
    if .type == "assistant" then
      (.message.content // []) | .[] |
      if .type == "text" then
        "[text] " + (.text | ltrimstr("\n") | .[0:200])
      elif .type == "tool_use" then
        "[tool: " + .name + "] " + (.input | tostring | .[0:120])
      else empty end
    elif .type == "result" then
      if .is_error then "[FAILED] " + (.result // "unknown error")
      else "[OK] done"
      end
    else empty end
  '
fi

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
    echo "${_C_YELLOW}${_C_BOLD}[${label}]${_C_RESET} step 1/2: jq missing, running claude without live parse" >&2
    if [[ -n "$tee_file" ]]; then
      "$@" --output-format stream-json --verbose | tee "$tee_file" >/dev/null
      return ${PIPESTATUS[0]}
    fi
    "$@" --output-format stream-json --verbose
    return $?
  fi

  echo "${_C_CYAN}${_C_BOLD}[${label}]${_C_RESET} step 1/2: 启动 claude (stream-json 模式)" >&2

  # Heartbeat in background; trap EXIT on the current shell (function scope
  # cannot install function-local traps in bash 3.2, so install on the caller
  # shell and clear at the end). To stay isolated, use a subshell instead.
  local rc=0
  (
    _cortex_heartbeat "$label" &
    local hb_pid=$!
    # shellcheck disable=SC2064
    trap "kill $hb_pid 2>/dev/null; wait $hb_pid 2>/dev/null" EXIT INT TERM

    echo "${_C_CYAN}${_C_BOLD}[${label}]${_C_RESET} step 2/2: 等待 claude 输出..." >&2

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
    echo "${_C_GREEN}${_C_BOLD}[${label}] OK${_C_RESET}" >&2
  else
    echo "${_C_RED}${_C_BOLD}[${label}] FAILED: exit code $rc${_C_RESET}" >&2
  fi
  return $rc
}
