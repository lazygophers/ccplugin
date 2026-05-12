#!/usr/bin/env bash
# cortex/scripts/cron/lint.sh — daily lint of the cortex vault via claude --bare.
#
# Usage:
#   lint.sh [--dry-run] [--sync-templates] [--vault <path>] [--lang <code>] [--settings <path>]
#
# Wraps run.sh with the lint prompt. Default read-only (allowed-tools = Bash Read Glob Grep).
# With --sync-templates: also allows Write/Edit so AI can auto-sync template/seed drift
# (rules: template-outdated / template-missing / seed-outdated only).
#
# Config-only per PRD: reads ~/.cortex/config.json. CLI flags override.

set -uo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/../.." && pwd)"
# shellcheck source=../lib/config.sh
source "$DIR/../lib/config.sh"
cortex_config_init

DRY_FLAG=()
VAULT_FLAG=()
LANG_FLAG=()
SETTINGS_FLAG=()
CLI_VAULT=""
CLI_LANG=""
SYNC_TEMPLATES=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)        DRY_FLAG=(--dry-run);                  shift ;;
    --sync-templates) SYNC_TEMPLATES=1;                      shift ;;
    --vault)          CLI_VAULT="$2"; VAULT_FLAG=(--vault "$2"); shift 2 ;;
    --lang)           CLI_LANG="$2";  LANG_FLAG=(--lang "$2");   shift 2 ;;
    --settings)       SETTINGS_FLAG=(--settings "$2");           shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 4 ;;
  esac
done

VAULT="${CLI_VAULT:-$(cx_get_vault)}"
if [[ -z "$VAULT" ]]; then
  echo "[cortex/lint] no vault: pass --vault or set 'vault' in ~/.cortex/config.json" >&2
  exit 3
fi
LANG_CODE="${CLI_LANG:-$(cx_config_get lang "")}"

SYNC_HINT=""
ALLOWED_TOOLS="Bash Read Glob Grep"
if [[ "$SYNC_TEMPLATES" == "1" ]]; then
  ALLOWED_TOOLS="Bash Read Glob Grep Write Edit"
  SYNC_HINT="

NOTE: caller passed --sync-templates. Before the read-only
report, invoke lint/run.py with --sync-templates once to auto-sync template-outdated /
template-missing / seed-outdated drift (those rules only; other fixable findings remain
reported, not modified). Then run the regular lint report."
fi

PROMPT="Run cortex-lint on the vault at $VAULT (use lang ${LANG_CODE:-zh-CN}).
Output the lint summary as compact JSON with errors/warns/rules_hit.
Use the cortex-lint skill (read-only by default, do not autofix in cron unless --sync-templates set).
Tool budget: ${ALLOWED_TOOLS}.${SYNC_HINT}"

exec "$DIR/run.sh" lint \
  ${VAULT_FLAG[@]+"${VAULT_FLAG[@]}"} \
  ${LANG_FLAG[@]+"${LANG_FLAG[@]}"} \
  ${SETTINGS_FLAG[@]+"${SETTINGS_FLAG[@]}"} \
  ${DRY_FLAG[@]+"${DRY_FLAG[@]}"} \
  -- "$PROMPT" \
  --allowed-tools "$ALLOWED_TOOLS"
