#!/usr/bin/env bash
# cortex/scripts/cron/fold.sh — weekly log fold via claude --bare.
#
# Usage:
#   fold.sh [--dry-run] [--vault <path>] [--lang <code>] [--settings <path>]
#
# Config-only per PRD: reads ~/.cortex/config.json. CLI flags override.

set -uo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/config.sh
source "$DIR/../lib/config.sh"
cortex_config_init

DRY_FLAG=()
VAULT_FLAG=()
LANG_FLAG=()
SETTINGS_FLAG=()
CLI_VAULT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)  DRY_FLAG=(--dry-run);              shift ;;
    --vault)    CLI_VAULT="$2"; VAULT_FLAG=(--vault "$2"); shift 2 ;;
    --lang)     LANG_FLAG=(--lang "$2");           shift 2 ;;
    --settings) SETTINGS_FLAG=(--settings "$2");   shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 4 ;;
  esac
done

# Resolve vault for prompt interpolation (CLI > config).
VAULT="${CLI_VAULT:-$(cx_get_vault)}"
if [[ -z "$VAULT" ]]; then
  echo "[cortex/fold] no vault: pass --vault or set 'vault' in ~/.cortex/config.json" >&2
  exit 3
fi

# fold writes — give a wider timeout than lint
TIMEOUT_FLAG=(--timeout 600)

PROMPT="Run cortex-fold on the vault at $VAULT.
Default --days 7 keep window. Apply changes (\\\`--apply\\\`) if invoked from weekly cron.
Tool budget: Bash Read Write Edit Glob.
Output one-line JSON summary: { folded: N, written: <fold paths>, kept: M }."

exec "$DIR/run.sh" fold \
  ${VAULT_FLAG[@]+"${VAULT_FLAG[@]}"} ${LANG_FLAG[@]+"${LANG_FLAG[@]}"} ${SETTINGS_FLAG[@]+"${SETTINGS_FLAG[@]}"} \
  ${TIMEOUT_FLAG[@]+"${TIMEOUT_FLAG[@]}"} ${DRY_FLAG[@]+"${DRY_FLAG[@]}"} \
  -- "$PROMPT" \
  --allowed-tools "Bash Read Write Edit Glob"
