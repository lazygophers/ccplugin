#!/usr/bin/env bash
# cortex/scripts/lib/config.sh — bash counterpart of hooks/_lib/cortex_config.py
#
# Source from other bash scripts:
#   source "$(dirname "${BASH_SOURCE[0]}")/../lib/config.sh"
#
# Provides:
#   cortex_config_init
#     MUST be called once from the top of the caller script BEFORE any
#     `cortex_config_resolve "$(...)"`. Validates `~/.cortex/config.json`
#     syntax and exits the caller process with code 1 on failure. This
#     cannot be folded into `cortex_config_resolve` because the resolve
#     is almost always invoked inside `$(...)` — an `exit` there only
#     kills the subshell, so a broken-JSON error would not fail-fast.
#
#   cortex_config_resolve <key> <env_var> <fallback>
#     Echo the resolved value with priority: env > config > fallback.
#     Empty-string env/config values fall through to the next source.
#     Safe to call inside command substitution.
#
# Behavior parity with the Python loader:
#   - File absent  -> treated as empty config (no error)
#   - jq missing   -> empty config, one-shot stderr warning
#   - JSON broken  -> fail-fast (exit 1) with "config syntax error at <path>: <detail>"
#   - Non-object   -> fail-fast (same message)
#   - Empty string -> fall through (not a real value)
#
# This file is sourced, never executed directly. Functions enforce `set -u`
# style guards internally; callers are not required to use `set -euo pipefail`.

# Resolve config path lazily so tests can monkeypatch $HOME.
_cortex_config_path() {
  printf '%s/.cortex/config.json' "${HOME:-$(printf '%s' ~)}"
}

# One-shot warn flag for missing jq.
_CORTEX_JQ_WARNED="${_CORTEX_JQ_WARNED:-0}"

# Public: validate `~/.cortex/config.json` from the caller's process so
# `exit 1` actually terminates the script (not a $() subshell). Idempotent.
cortex_config_init() {
  _cortex_config_validate
}

# Validate `~/.cortex/config.json` parses as a JSON object.
# Exit 1 with stderr message on failure. No-op when file/jq absent.
# MUST be called from the caller's scope (not inside $()) so `exit 1` propagates.
_cortex_config_validate() {
  local path
  path="$(_cortex_config_path)"
  if [[ ! -e "$path" ]]; then
    return 0
  fi
  if ! command -v jq >/dev/null 2>&1; then
    if [[ "$_CORTEX_JQ_WARNED" != "1" ]]; then
      echo "[cortex] warning: jq not installed; ignoring $path" >&2
      _CORTEX_JQ_WARNED=1
    fi
    return 0
  fi
  local err rc
  err="$(jq -e 'type == "object"' "$path" 2>&1 >/dev/null)"
  rc=$?
  if [[ $rc -eq 0 ]]; then
    return 0
  fi
  # `jq -e` exits non-zero either on parse error OR when the expression is
  # false (root is not an object).
  if [[ "$err" == *"parse error"* || "$err" == *"Could not"* || "$err" == *"Invalid"* ]]; then
    echo "config syntax error at $path: ${err}" >&2
  else
    echo "config syntax error at $path: root must be a JSON object" >&2
  fi
  exit 1
}

# Read a single top-level string field from ~/.cortex/config.json.
# Echoes the value (empty if unset / file absent / jq absent).
# Assumes _cortex_config_validate has been called already; safe to invoke
# inside command substitution.
_cortex_config_get() {
  local key="${1:-}"
  if [[ -z "$key" ]]; then
    return 0
  fi
  local path
  path="$(_cortex_config_path)"
  if [[ ! -e "$path" ]]; then
    return 0
  fi
  if ! command -v jq >/dev/null 2>&1; then
    return 0
  fi
  jq -r --arg k "$key" '.[$k] // empty' "$path" 2>/dev/null
}

# Resolve a value: env > config > fallback. Empty strings fall through.
cortex_config_resolve() {
  local key="${1:-}"
  local env_var="${2:-}"
  local fallback="${3:-}"
  local val=""
  if [[ -n "$env_var" ]]; then
    # Indirect lookup; safe under `set -u` because we default to "".
    val="${!env_var:-}"
    if [[ -n "$val" ]]; then
      printf '%s' "$val"
      return 0
    fi
  fi
  # Note: JSON syntax validation happens in `cortex_config_init`, which
  # callers must invoke once at script start. We deliberately do NOT call
  # `_cortex_config_validate` here because this function is normally
  # invoked inside `$(...)`, where `exit 1` would only kill the subshell.
  val="$(_cortex_config_get "$key")"
  if [[ -n "$val" ]]; then
    printf '%s' "$val"
    return 0
  fi
  printf '%s' "$fallback"
}

# --- Config-only helpers (env-free) -------------------------------------
# Plugin business code uses these instead of `cortex_config_resolve` for
# config-class keys. Env vars are reserved for platform-contract
# (CLAUDE_PLUGIN_ROOT) and internal runtime communication
# (CORTEX_JOB_LABEL, CORTEX_STREAM_TEE_FILE).

cx_config_get() {
  # cx_config_get <key> [default]
  local key="${1:-}"
  local default="${2:-}"
  local val
  val="$(_cortex_config_get "$key")"
  if [[ -n "$val" ]]; then
    printf '%s' "$val"
    return 0
  fi
  printf '%s' "$default"
}

cx_get_vault()       { cx_config_get vault ""; }
cx_get_plugin_root() { cx_config_get install_path ""; }
cx_get_lang()        { cx_config_get lang "zh-CN"; }
cx_get_settings()    { cx_config_get settings "$HOME/.claude/settings.json"; }
cx_get_timeout()     { cx_config_get timeout_default "${1:-300}"; }
