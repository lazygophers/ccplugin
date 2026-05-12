#!/usr/bin/env bash
# Tests for hooks/session_start.sh
# Per PRD: plugin business is env-free; vault is read from $HOME/.cortex/config.json.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/../.." && pwd)"
# shellcheck source=./_assert.sh
source "$DIR/_assert.sh"

SCRIPT="$PLUGIN_ROOT/hooks/session_start.sh"

# Build a minimal vault on tmp.
make_vault() {
  local root="$1" lang="${2:-zh-CN}"
  mkdir -p "$root/.obsidian" "$root/_meta" "$root/log" "$root/folds"
  printf '{"lang":"%s","preset":"lyt"}\n' "$lang" > "$root/_meta/version.json"
  : > "$root/index.md"
}

# Create a fake HOME containing ~/.cortex/config.json that points at vault.
make_home_with_vault() {
  local home="$1" vault="$2"
  mkdir -p "$home/.cortex"
  printf '{"vault": "%s"}\n' "$vault" > "$home/.cortex/config.json"
}

run_hook() {
  local vault="$1"
  local home; home=$(mktemp -d)
  make_home_with_vault "$home" "$vault"
  CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" HOME="$home" \
    bash "$SCRIPT" </dev/null 2>/dev/null
}

test_vault_present_outputs_v2_json() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_vault "$sandbox/v" zh-CN
  out=$(run_hook "$sandbox/v")
  assert_contains "hookSpecificOutput" "$out"
  assert_contains "SessionStart" "$out"
  assert_contains "additionalContext" "$out"
  local home; home=$(mktemp -d)
  make_home_with_vault "$home" "$sandbox/v"
  CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" HOME="$home" \
    bash "$SCRIPT" </dev/null > /dev/null 2>/dev/null
  assert_eq "0" "$?"
}

test_vault_missing_silent_exit_0() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  out=$(env -i \
        PATH="$PATH" \
        CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" \
        HOME="$sandbox/empty-home" \
        bash "$SCRIPT" </dev/null 2>/dev/null)
  assert_empty "$out" "vault missing -> stdout empty"
}

test_lang_in_output() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_vault "$sandbox/v" en
  out=$(run_hook "$sandbox/v")
  assert_contains "lang=en" "$out"
}

test_handles_empty_stdin() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_vault "$sandbox/v"
  local home; home=$(mktemp -d)
  make_home_with_vault "$home" "$sandbox/v"
  CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" HOME="$home" \
    bash "$SCRIPT" </dev/null > /dev/null 2>/dev/null
  assert_eq "0" "$?"
}

run_test test_vault_present_outputs_v2_json  test_vault_present_outputs_v2_json
run_test test_vault_missing_silent_exit_0    test_vault_missing_silent_exit_0
run_test test_lang_in_output                 test_lang_in_output
run_test test_handles_empty_stdin            test_handles_empty_stdin

print_summary
