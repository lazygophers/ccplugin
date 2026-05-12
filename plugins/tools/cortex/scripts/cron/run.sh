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
# Configuration: read from ~/.cortex/config.json (env-free per PRD); the
# calling script may override per-invocation via CLI flags below.
#
# CLI flags (placed BEFORE `--`):
#   --vault <path>      override config.vault
#   --lang  <code>      override config.lang
#   --settings <path>   override config.settings
#   --timeout <secs>    override config.timeout_default (or 300)
#   --dry-run           print the resolved command and exit 0
#
# Internal runtime env (NOT user config — kept):
#   CORTEX_JOB_LABEL        wrapper identifier consumed by cortex_stream
#   CORTEX_STREAM_TEE_FILE  NDJSON tee path consumed by cortex_stream
#
# Exit codes:
#   0  success
#   1  generic failure (claude said is_error=true, or jq parse failed)
#   2  lock busy (another instance running)
#   3  timeout
#   4  config / argument error

set -uo pipefail

# ── helpers ─────────────────────────────────────────────────────────
# ISO8601 UTC timestamp (grep-friendly, locale-independent)
iso_now() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

# cron 跑完自动 git commit vault 变更 (不 push); 非 git repo / 无变更静默跳
cx_git_commit_vault() {
  local job="${1:-cortex}"
  local config="$HOME/.cortex/config.json"
  [[ -f "$config" ]] || return 0
  command -v jq >/dev/null 2>&1 || return 0
  command -v git >/dev/null 2>&1 || return 0
  local vault
  vault=$(jq -r '.vault // empty' "$config" 2>/dev/null) || return 0
  [[ -n "$vault" && -d "$vault/.git" ]] || return 0
  (
    cd "$vault" 2>/dev/null || exit 0
    if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
      git add -A 2>/dev/null && \
      git commit -m "[cortex/$job] auto $(date -u +%Y-%m-%dT%H:%M:%SZ)" --no-verify -q 2>/dev/null
    fi
  ) || true
}

# resolve_timeout_cmd: print "gtimeout" / "timeout" / "PERL_TIMEOUT" sentinel,
# return non-zero if none available. macOS lacks GNU `timeout(1)` by default.
resolve_timeout_cmd() {
  if command -v gtimeout >/dev/null 2>&1; then
    echo "gtimeout"
    return 0
  fi
  if command -v timeout >/dev/null 2>&1; then
    echo "timeout"
    return 0
  fi
  if command -v perl >/dev/null 2>&1; then
    echo "PERL_TIMEOUT"
    return 0
  fi
  return 1
}

# perl_timeout SECS CMD [ARGS...] — pure-perl alarm wrapper.
# Exit 124 on timeout (matching GNU timeout); otherwise propagates child rc.
perl_timeout() {
  local secs="$1"; shift
  perl -e '
    use strict; use warnings;
    my $secs = shift @ARGV;
    my $pid = fork();
    die "fork: $!" unless defined $pid;
    if ($pid == 0) { exec @ARGV; die "exec: $!"; }
    eval {
      local $SIG{ALRM} = sub { die "timeout\n"; };
      alarm $secs;
      waitpid($pid, 0);
      alarm 0;
      exit($? >> 8);
    };
    if ($@ =~ /^timeout/) {
      kill 9, $pid;
      waitpid($pid, 0);
      exit 124;
    }
    exit 1;
  ' "$secs" "$@"
}

JOB="${1:-}"
shift || true
if [[ -z "$JOB" ]]; then
  echo "usage: run.sh <job-name> [--vault X --lang Y ...] -- <prompt> [extra flags...]" >&2
  exit 4
fi

# Parse leading option flags (BEFORE `--`). Empty values fall through to config.
CLI_VAULT=""
CLI_LANG=""
CLI_SETTINGS=""
CLI_TIMEOUT=""
CLI_DRY_RUN=0
while [[ "${1:-}" != "--" && $# -gt 0 ]]; do
  case "$1" in
    --vault)    CLI_VAULT="${2:-}";    shift 2 ;;
    --lang)     CLI_LANG="${2:-}";     shift 2 ;;
    --settings) CLI_SETTINGS="${2:-}"; shift 2 ;;
    --timeout)  CLI_TIMEOUT="${2:-}";  shift 2 ;;
    --dry-run)  CLI_DRY_RUN=1;         shift ;;
    *) break ;;
  esac
done
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
# shellcheck source=../lib/stream_progress.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib/stream_progress.sh"
# Validate ~/.cortex/config.json in this process so broken JSON fails fast.
cortex_config_init

# Resolution priority (env-free per PRD): CLI flag > ~/.cortex/config.json > default.
VAULT="${CLI_VAULT:-$(cx_get_vault)}"
if [[ -z "$VAULT" ]]; then
  echo "[cortex] no vault: pass --vault <path> or set 'vault' in ~/.cortex/config.json" >&2
  exit 3
fi
# lang: CLI > config; vault `_meta/version.json` is layered on top by Python
# consumers (lint/run.py, hooks/_lib/cortex_locale.py).
LANG_OVERRIDE="${CLI_LANG:-$(cx_config_get lang "")}"
SETTINGS="${CLI_SETTINGS:-$(cx_config_get settings "$HOME/.claude/settings.glm-4.7-flash.json")}"
TIMEOUT="${CLI_TIMEOUT:-$(cx_config_get timeout_default 300)}"

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
    echo "[$(iso_now)] cortex-${JOB}: lock busy ($LOCK), skipping" | tee -a "$LOG_FILE" >&2
    exit 2
  fi
else
  # macOS / no flock — best-effort PID lockfile
  if [[ -f "$LOCK" ]] && kill -0 "$(cat "$LOCK" 2>/dev/null)" 2>/dev/null; then
    echo "[$(iso_now)] cortex-${JOB}: pid lock busy ($LOCK), skipping" | tee -a "$LOG_FILE" >&2
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
  --max-budget-usd 0.30
  -p "$FULL_PROMPT"
)
# Note: --output-format stream-json --verbose is injected by cortex_stream_runner.

# Append any extra flags (e.g. --allowed-tools)
for arg in "$@"; do
  CMD+=("$arg")
done

if [[ "$CLI_DRY_RUN" == "1" ]]; then
  printf '[dry-run] %q ' "${CMD[@]}"
  echo
  exit 0
fi

echo "[$(iso_now)] cortex-${JOB}: start" >> "$LOG_FILE"

# Run with timeout; pipe to jq to extract result line
TMP_NDJSON="$(mktemp)"
trap 'rm -f "$TMP_NDJSON"; cx_git_commit_vault "cortex-${JOB}"' EXIT

export CORTEX_JOB_LABEL="cortex-${JOB}"
export CORTEX_STREAM_TEE_FILE="$TMP_NDJSON"
# cortex_stream_runner reads CORTEX_TIMEOUT and forwards it to cortex_stream.py
# via `--timeout`. Inline (in-process) timeout is enforced by the python wrapper
# — no external `timeout(1)` / `perl_timeout` binary is needed here, which
# avoids the "bash function not on PATH" failure when Python's subprocess.Popen
# is given a bash function name as argv[0].
export CORTEX_TIMEOUT="$TIMEOUT"

# stderr routing:
#   - tty (interactive, e.g. ~/.cortex/scripts/lint.sh in a terminal):
#       stream_progress.sh stderr (rich Live UI, heartbeat, step logs) is
#       tee'd to ERR_FILE *and* forwarded back to the user's terminal.
#   - non-tty (cron / pipe): stderr only appended to ERR_FILE (unchanged
#       legacy behaviour, keeps cron logs silent on stdout/stderr).
# bash 3.2 supports process substitution `>(...)`, which is required here.
# NDJSON is captured via CORTEX_STREAM_TEE_FILE=$TMP_NDJSON (env above);
# stdout passthrough from cortex_stream.py is discarded to keep the
# terminal clean — only the rich UI on stderr is shown to the user.
if [[ -t 2 ]]; then
  cortex_stream_runner "${CMD[@]}" \
    2> >(tee -a "$ERR_FILE" >&2) \
    > /dev/null
else
  cortex_stream_runner "${CMD[@]}" 2>>"$ERR_FILE" > /dev/null
fi
rc=$?
if [[ $rc -ne 0 ]]; then
  if [[ $rc -eq 124 ]]; then
    echo "[$(iso_now)] cortex-${JOB}: TIMEOUT after ${TIMEOUT}s" | tee -a "$LOG_FILE" >&2
    exit 3
  fi
  echo "[$(iso_now)] cortex-${JOB}: claude exited rc=$rc" | tee -a "$LOG_FILE" >&2
  exit 1
fi

# Filter result line
if ! jq -c 'select(.type=="result")' "$TMP_NDJSON" > "$RESULT_FILE" 2>>"$ERR_FILE"; then
  echo "[$(iso_now)] cortex-${JOB}: jq parse failed" | tee -a "$LOG_FILE" >&2
  exit 1
fi

if [[ ! -s "$RESULT_FILE" ]]; then
  echo "[$(iso_now)] cortex-${JOB}: no result line in stream" | tee -a "$LOG_FILE" >&2
  exit 1
fi

is_error="$(jq -r '.is_error' "$RESULT_FILE")"
if [[ "$is_error" == "true" ]]; then
  err_msg="$(jq -r '.result // .error // "(no message)"' "$RESULT_FILE")"
  echo "[$(iso_now)] cortex-${JOB}: result.is_error=true: $err_msg" | tee -a "$LOG_FILE" >&2
  exit 1
fi

echo "[$(iso_now)] cortex-${JOB}: success" >> "$LOG_FILE"
exit 0
