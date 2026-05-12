#!/usr/bin/env bash
# cortex/scripts/lib/stream_progress.sh
#
# Stream-json progress visibility library for cortex wrappers.
#
# Phase A (rich): delegates parse/heartbeat to the `cortex_stream.py`
# script (shipped under <plugin>/mcp/), executed via system python3 with
# `rich` installed (pip3 install --user). This file is a thin shim that:
#   - keeps tty-aware ANSI color variables (other scripts may reuse them);
#   - keeps cortex_check_jq (legacy callers still probe jq);
#   - dispatches to python3 + cortex_stream.py when rich is available,
#     falls back to raw exec otherwise (no progress UI, but no crash).
#
# Source-only library (no top-level side effects, idempotent to re-source).
# Usage:
#   source "$LIB_PATH"
#   export CORTEX_JOB_LABEL="cortex-doctor"        # optional, default "cortex"
#   export CORTEX_STREAM_TEE_FILE="/tmp/x.ndjson"  # optional, capture raw NDJSON
#   cortex_stream_runner claude --bare -p "..."    # auto-injects stream-json
#
# Contract:
#   - cortex-stream auto-appends `--output-format stream-json --verbose` and
#     tees raw NDJSON to $CORTEX_STREAM_TEE_FILE if set.
#   - Stdout is the raw NDJSON passthrough (downstream run.sh parses the
#     trailing result line); stderr carries the rich Live UI.
#   - Return code is the wrapped command's exit code.

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
else
  _C_RESET=""
  _C_BOLD=""
  _C_DIM=""
  _C_CYAN=""
  _C_GREEN=""
  _C_YELLOW=""
  _C_RED=""
  _C_MAGENTA=""
fi

# Detect jq availability. Sets CORTEX_NO_JQ=1 on absence, returns non-zero.
# Retained for legacy callers that probe jq independently of stream parsing.
cortex_check_jq() {
  if command -v jq >/dev/null 2>&1; then
    return 0
  fi
  CORTEX_NO_JQ=1
  return 1
}

# cortex_stream_runner CMD [ARGS...]
#
# Delegates stream-json parsing + heartbeat + step rendering to the
# `cortex_stream.py` script (rich-based) shipped under <plugin>/mcp/.
# The python entrypoint auto-appends
# `--output-format stream-json --verbose`, tees raw NDJSON to
# $CORTEX_STREAM_TEE_FILE if set, and passes through to stdout so
# downstream callers (run.sh) can still parse the result line.
#
# Fallback: if system python3 lacks rich and no cortex-stream is on
# PATH, run the command raw with stream-json flags — no progress UI,
# but no crash either.
#
# Optional env:
#   CORTEX_JOB_LABEL       — label prefix (default "cortex")
#   CORTEX_STREAM_TEE_FILE — raw NDJSON capture path
#
# Exit code: child command's exit code.
cortex_stream_runner() {
  local label="${CORTEX_JOB_LABEL:-cortex}"
  local tee_file="${CORTEX_STREAM_TEE_FILE:-}"
  # CORTEX_TIMEOUT (seconds): forwarded to cortex_stream.py as --timeout.
  # 0 disables. cortex_stream.py enforces deadline + SIGKILL → return 124,
  # matching GNU timeout(1) so run.sh's rc=124 → exit 3 mapping still works.
  local timeout="${CORTEX_TIMEOUT:-0}"

  # Infer plugin_root from this file's location (<root>/scripts/lib/stream_progress.sh).
  # Env override takes priority: CORTEX_PLUGIN_ROOT > CLAUDE_PLUGIN_ROOT > self-derive.
  local _sp_dir
  _sp_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)" || _sp_dir=""
  local plugin_root="${CORTEX_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}"
  if [[ -z "$plugin_root" && -n "$_sp_dir" ]]; then
    plugin_root="$(cd "$_sp_dir/../.." 2>/dev/null && pwd)"
  fi
  local stream_script="$plugin_root/mcp/cortex_stream.py"

  # Path 1 (preferred): system python3 with rich (用户偏好: 不走 venv).
  if [[ -f "$stream_script" ]] && command -v python3 >/dev/null 2>&1; then
    if python3 -c "import rich" 2>/dev/null; then
      python3 "$stream_script" --label "$label" --timeout "$timeout" -- "$@"
      return $?
    fi
  fi

  # Path 2: cortex-stream console-script on PATH (向后兼容, 用户若手动装仍可用).
  if command -v cortex-stream >/dev/null 2>&1; then
    cortex-stream --label "$label" --timeout "$timeout" -- "$@"
    return $?
  fi

  # Path 3: raw fallback — warn, preserve stream-json + verbose so run.sh tee still works.
  echo "${_C_YELLOW}${_C_BOLD}[${label}]${_C_RESET} rich not available (try: pip3 install rich), no progress UI" >&2
  if [[ -n "$tee_file" ]]; then
    "$@" --output-format stream-json --verbose | tee "$tee_file" >/dev/null
    return ${PIPESTATUS[0]}
  fi
  "$@" --output-format stream-json --verbose
  return $?
}
