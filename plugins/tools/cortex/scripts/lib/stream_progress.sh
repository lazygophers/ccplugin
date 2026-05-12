#!/usr/bin/env bash
# cortex/scripts/lib/stream_progress.sh
#
# Stream-json progress visibility library for cortex wrappers.
#
# Phase A (rich): delegates parse/heartbeat to the `cortex-stream` python
# console-script (exposed by cortex-mcp pipx install) instead of jq + bash
# background heartbeat. This file is now a thin shim that:
#   - keeps tty-aware ANSI color variables (other scripts may reuse them);
#   - keeps cortex_check_jq (legacy callers still probe jq);
#   - dispatches to cortex-stream when available, falls back to raw exec
#     otherwise (no progress UI, but no crash either).
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
# `cortex-stream` python console-script (rich-based) exposed by the
# cortex-mcp pipx install. The python entrypoint auto-appends
# `--output-format stream-json --verbose`, tees raw NDJSON to
# $CORTEX_STREAM_TEE_FILE if set, and passes through to stdout so
# downstream callers (run.sh) can still parse the result line.
#
# Fallback: if cortex-stream is not on PATH (pipx not installed yet),
# run the command raw with stream-json flags — no progress UI, but
# no crash either.
#
# Optional env:
#   CORTEX_JOB_LABEL       — label prefix (default "cortex")
#   CORTEX_STREAM_TEE_FILE — raw NDJSON capture path
#
# Exit code: child command's exit code.
cortex_stream_runner() {
  local label="${CORTEX_JOB_LABEL:-cortex}"
  local tee_file="${CORTEX_STREAM_TEE_FILE:-}"

  if command -v cortex-stream >/dev/null 2>&1; then
    cortex-stream --label "$label" -- "$@"
    return $?
  fi

  echo "${_C_YELLOW}${_C_BOLD}[${label}]${_C_RESET} cortex-stream not in PATH (pipx install cortex-mcp), no progress UI" >&2
  if [[ -n "$tee_file" ]]; then
    "$@" --output-format stream-json --verbose | tee "$tee_file" >/dev/null
    return ${PIPESTATUS[0]}
  fi
  "$@" --output-format stream-json --verbose
  return $?
}
