#!/usr/bin/env bash
# Tests for hooks/_lib/resolve_vault.sh
# Per PRD: plugin business is env-free; vault is read from ~/.cortex/config.json.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/../.." && pwd)"
# shellcheck source=./_assert.sh
source "$DIR/_assert.sh"

RV="$PLUGIN_ROOT/hooks/_lib/resolve_vault.sh"

# Run the resolver in a subshell with controlled HOME so we don't pollute parent.
run_rv() {
  bash -c '
    unset OBSIDIAN_VAULT CORTEX_VAULT CORTEX_VAULT_PATH
    export HOME="$1"
    source "$2"
    resolve_vault
  ' _ "$1" "$RV"
}

write_config() {
  # write_config <home> <vault>
  local home="$1" vault="$2"
  mkdir -p "$home/.cortex"
  printf '{"vault": "%s"}\n' "$vault" > "$home/.cortex/config.json"
}

test_env_ignored_for_vault() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  # Even with OBSIDIAN_VAULT set (legacy), resolve_vault must ignore it.
  local custom="$sandbox/custom-vault"
  mkdir -p "$custom/.obsidian"
  out=$(OBSIDIAN_VAULT="$custom" bash -c '
    export HOME="$1"
    source "$2"
    resolve_vault
  ' _ "$sandbox/home" "$RV")
  assert_empty "$out" "OBSIDIAN_VAULT env should be ignored (PRD: config-only)"
}

test_config_json_resolves() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  local home="$sandbox/home"; mkdir -p "$home"
  local vault="$sandbox/myvault"; mkdir -p "$vault/.obsidian"
  write_config "$home" "$vault"
  out=$(run_rv "$home")
  assert_eq "$vault" "$out"
}

test_missing_returns_empty() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  local home="$sandbox/home"; mkdir -p "$home"
  out=$(run_rv "$home")
  assert_empty "$out"
}

test_exit_code_zero_always() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  local home="$sandbox/home"; mkdir -p "$home"
  run_rv "$home" > /dev/null
  assert_eq "0" "$?" "resolve_vault should always exit 0 (advisory)"
}

run_test test_env_ignored_for_vault  test_env_ignored_for_vault
run_test test_config_json_resolves   test_config_json_resolves
run_test test_missing_returns_empty  test_missing_returns_empty
run_test test_exit_code_zero_always  test_exit_code_zero_always

print_summary
