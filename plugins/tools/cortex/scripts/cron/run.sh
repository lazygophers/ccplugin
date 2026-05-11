#!/usr/bin/env bash
# cortex/scripts/cron/run.sh — generic wrapper for periodic cortex maintenance via `claude --bare -p`.
#
# Provides:
#   - flock-based mutex per job
#   - timeout (default 300s)
#   - log rotation (keep 7 days under ~/.cache/cortex/cron/)
#   - structured exit codes
#
# Usage:
#   run.sh <job-name> -- <claude prompt> [extra claude flags...]
#
# Env / flags consumed (passed via the calling script):
#   CORTEX_VAULT       (required) vault root path; printed into prompt context
#   CORTEX_LANG        (optional) override vault.lang; default detected from _meta/version.json
#   CORTEX_SETTINGS    (optional) path to claude settings json; default ~/.claude/settings.glm-4.5-flash.json
#   CORTEX_TIMEOUT     (optional) seconds; default 300
#   CORTEX_DRY_RUN=1   (optional) print the resolved command and exit 0
#
# Exit codes:
#   0  success
#   1  generic failure (claude said is_error=true, or jq parse failed)
#   2  lock busy (another instance running)
#   3  timeout
#   4  config / argument error

set -uo pipefail

JOB="${1:-}"
shift || true
if [[ -z "$JOB" ]]; then
  echo "usage: run.sh <job-name> -- <prompt> [extra flags...]" >&2
  exit 4
fi

if [[ "${1:-}" == "--" ]]; then
  shift
fi

PROMPT="${1:-}"
shift || true
if [[ -z "$PROMPT" ]]; then
  echo "missing prompt for job=$JOB" >&2
  exit 4
fi

# shellcheck source=../lib/config.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/config.sh"
# Validate ~/.cortex/config.json in this process so broken JSON fails fast.
cortex_config_init

VAULT="$(cortex_config_resolve vault CORTEX_VAULT "")"
if [[ -z "$VAULT" ]]; then
  VAULT="${OBSIDIAN_VAULT:-}"
fi
if [[ -z "$VAULT" ]]; then
  echo "[cortex] no vault: set CORTEX_VAULT, OBSIDIAN_VAULT, or write vault to ~/.cortex/config.json" >&2
  exit 3
fi
# lang priority here is env > config; vault `_meta/version.json` is layered on
# top by Python consumers (lint/run.py, hooks/_lib/cortex_locale.py).
LANG_OVERRIDE="$(cortex_config_resolve lang CORTEX_LANG "")"
SETTINGS="$(cortex_config_resolve settings CORTEX_SETTINGS "$HOME/.claude/settings.glm-4.5-flash.json")"
TIMEOUT="${CORTEX_TIMEOUT:-300}"

LOG_DIR="$HOME/.cache/cortex/cron"
mkdir -p "$LOG_DIR"
DAY="$(date +%F)"
LOG_FILE="$LOG_DIR/${JOB}-${DAY}.log"
ERR_FILE="$LOG_DIR/${JOB}-${DAY}.err"
RESULT_FILE="$LOG_DIR/${JOB}-${DAY}.json"

# rotate: drop logs older than 7 days
find "$LOG_DIR" -type f -mtime +7 -name "*.log" -delete 2>/dev/null || true
find "$LOG_DIR" -type f -mtime +7 -name "*.err" -delete 2>/dev/null || true
find "$LOG_DIR" -type f -mtime +7 -name "*.json" -delete 2>/dev/null || true

LOCK="/tmp/cortex-${JOB}.lock"
if command -v flock >/dev/null 2>&1; then
  exec 9>"$LOCK"
  if ! flock -n 9; then
    echo "[$(date)] cortex-${JOB}: lock busy ($LOCK), skipping" | tee -a "$LOG_FILE" >&2
    exit 2
  fi
else
  # macOS / no flock — best-effort PID lockfile
  if [[ -f "$LOCK" ]] && kill -0 "$(cat "$LOCK" 2>/dev/null)" 2>/dev/null; then
    echo "[$(date)] cortex-${JOB}: pid lock busy ($LOCK), skipping" | tee -a "$LOG_FILE" >&2
    exit 2
  fi
  echo $$ > "$LOCK"
  trap 'rm -f "$LOCK"' EXIT
fi

# Build prompt with context header
FULL_PROMPT="vault: $VAULT
job: $JOB
$( [[ -n "$LANG_OVERRIDE" ]] && echo "lang_override: $LANG_OVERRIDE" )

$PROMPT"

CMD=(claude
  --bare
  --no-session-persistence
  --settings "$SETTINGS"
  --output-format stream-json
  --verbose
  --max-budget-usd 0.30
  -p "$FULL_PROMPT"
)

# Append any extra flags (e.g. --allowed-tools)
for arg in "$@"; do
  CMD+=("$arg")
done

if [[ "${CORTEX_DRY_RUN:-0}" == "1" ]]; then
  printf '[dry-run] %q ' "${CMD[@]}"
  echo
  exit 0
fi

echo "[$(date)] cortex-${JOB}: start" >> "$LOG_FILE"

# Run with timeout; pipe to jq to extract result line
TMP_NDJSON="$(mktemp)"
trap 'rm -f "$TMP_NDJSON"' EXIT

if ! timeout "$TIMEOUT" "${CMD[@]}" 2>>"$ERR_FILE" > "$TMP_NDJSON"; then
  rc=$?
  if [[ $rc -eq 124 ]]; then
    echo "[$(date)] cortex-${JOB}: TIMEOUT after ${TIMEOUT}s" | tee -a "$LOG_FILE" >&2
    exit 3
  fi
  echo "[$(date)] cortex-${JOB}: claude exited rc=$rc" | tee -a "$LOG_FILE" >&2
  exit 1
fi

# Filter result line
if ! jq -c 'select(.type=="result")' "$TMP_NDJSON" > "$RESULT_FILE" 2>>"$ERR_FILE"; then
  echo "[$(date)] cortex-${JOB}: jq parse failed" | tee -a "$LOG_FILE" >&2
  exit 1
fi

if [[ ! -s "$RESULT_FILE" ]]; then
  echo "[$(date)] cortex-${JOB}: no result line in stream" | tee -a "$LOG_FILE" >&2
  exit 1
fi

is_error="$(jq -r '.is_error' "$RESULT_FILE")"
if [[ "$is_error" == "true" ]]; then
  err_msg="$(jq -r '.result // .error // "(no message)"' "$RESULT_FILE")"
  echo "[$(date)] cortex-${JOB}: result.is_error=true: $err_msg" | tee -a "$LOG_FILE" >&2
  exit 1
fi

echo "[$(date)] cortex-${JOB}: success" >> "$LOG_FILE"
exit 0
