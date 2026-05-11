#!/usr/bin/env bash
# Tests for hooks/_lib/resolve_vault.sh
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/../.." && pwd)"
# shellcheck source=./_assert.sh
source "$DIR/_assert.sh"

RV="$PLUGIN_ROOT/hooks/_lib/resolve_vault.sh"

# Run the resolver in a subshell with controlled env so we don't pollute parent.
run_rv() {
  # args: env-var assignments... (no spaces). Final arg ignored.
  bash -c '
    unset OBSIDIAN_VAULT
    export HOME="$1"
    export XDG_CONFIG_HOME="$2"
    [[ -n "${3:-}" ]] && export OBSIDIAN_VAULT="$3"
    source "$4"
    resolve_vault
  ' _ "$1" "$2" "${3:-}" "$RV"
}

test_env_override_wins() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  local custom="$sandbox/custom-vault"
  mkdir -p "$custom/.obsidian"
  out=$(run_rv "$sandbox/home" "$sandbox/xdg" "$custom")
  assert_eq "$custom" "$out" "env override should win"
}

test_env_invalid_falls_through() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  # OBSIDIAN_VAULT points at a non-vault dir; should fall through to other layers
  local nope="$sandbox/not-a-vault"
  mkdir -p "$nope"
  out=$(run_rv "$sandbox/home" "$sandbox/xdg" "$nope")
  # nothing else exists → empty
  assert_empty "$out" "invalid env should fall through to empty"
}

test_config_json_resolves() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  local home="$sandbox/home"; mkdir -p "$home"
  local xdg="$sandbox/xdg/cortex"; mkdir -p "$xdg"
  local vault="$sandbox/myvault"; mkdir -p "$vault/.obsidian"
  printf '{"vault": "%s"}\n' "$vault" > "$xdg/config.json"
  out=$(run_rv "$home" "$sandbox/xdg" "")
  assert_eq "$vault" "$out"
}

test_missing_returns_empty() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  local home="$sandbox/home"; mkdir -p "$home"
  out=$(run_rv "$home" "$sandbox/xdg" "")
  assert_empty "$out"
}

test_exit_code_zero_always() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  local home="$sandbox/home"; mkdir -p "$home"
  run_rv "$home" "$sandbox/xdg" "" > /dev/null
  assert_eq "0" "$?" "resolve_vault should always exit 0 (advisory)"
}

run_test test_env_override_wins      test_env_override_wins
run_test test_env_invalid_falls_through  test_env_invalid_falls_through
run_test test_config_json_resolves   test_config_json_resolves
run_test test_missing_returns_empty  test_missing_returns_empty
run_test test_exit_code_zero_always  test_exit_code_zero_always

print_summary
