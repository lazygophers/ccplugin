#!/usr/bin/env bash
# Tests for hooks/session_start.sh
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/../.." && pwd)"
# shellcheck source=./_assert.sh
source "$DIR/_assert.sh"

SCRIPT="$PLUGIN_ROOT/hooks/session_start.sh"

# Build a minimal vault on tmp; OBSIDIAN_VAULT env makes resolve_vault use it.
make_vault() {
  local root="$1" lang="${2:-zh-CN}"
  mkdir -p "$root/.obsidian" "$root/_meta" "$root/log" "$root/folds"
  printf '{"lang":"%s","preset":"lyt"}\n' "$lang" > "$root/_meta/version.json"
  : > "$root/index.md"
}

# Run hook with given vault path; capture stdout
run_hook() {
  local vault="$1"
  CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" \
    OBSIDIAN_VAULT="$vault" \
    HOME="$(mktemp -d)" \
    bash "$SCRIPT" </dev/null 2>/dev/null
}

test_vault_present_outputs_v2_json() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_vault "$sandbox/v" zh-CN
  out=$(run_hook "$sandbox/v")
  assert_contains "hookSpecificOutput" "$out"
  assert_contains "SessionStart" "$out"
  assert_contains "additionalContext" "$out"
  # exit code zero
  CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" OBSIDIAN_VAULT="$sandbox/v" HOME="$(mktemp -d)" \
    bash "$SCRIPT" </dev/null > /dev/null 2>/dev/null
  assert_eq "0" "$?"
}

test_vault_missing_silent_exit_0() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  # No vault dir exists. resolve_vault won't find it via default path either.
  out=$(env -i \
        PATH="$PATH" \
        CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" \
        HOME="$sandbox/empty-home" \
        XDG_CONFIG_HOME="$sandbox/xdg-empty" \
        bash "$SCRIPT" </dev/null 2>/dev/null)
  assert_empty "$out" "vault missing -> stdout empty"
}

test_lang_in_output() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_vault "$sandbox/v" en
  out=$(run_hook "$sandbox/v")
  # lang en should appear somewhere in additionalContext
  assert_contains "lang=en" "$out"
}

test_handles_empty_stdin() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_vault "$sandbox/v"
  # explicit empty stdin
  CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" OBSIDIAN_VAULT="$sandbox/v" HOME="$(mktemp -d)" \
    bash "$SCRIPT" </dev/null > /dev/null 2>/dev/null
  assert_eq "0" "$?"
}

run_test test_vault_present_outputs_v2_json  test_vault_present_outputs_v2_json
run_test test_vault_missing_silent_exit_0    test_vault_missing_silent_exit_0
run_test test_lang_in_output                 test_lang_in_output
run_test test_handles_empty_stdin            test_handles_empty_stdin

print_summary
