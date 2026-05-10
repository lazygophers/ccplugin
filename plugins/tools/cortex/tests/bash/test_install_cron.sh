#!/usr/bin/env bash
# Tests for scripts/install_cron.sh
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/../.." && pwd)"
# shellcheck source=./_assert.sh
source "$DIR/_assert.sh"

SCRIPT="$PLUGIN_ROOT/scripts/install_cron.sh"

run_install() {
  CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" bash "$SCRIPT" "$@" 2>&1
}

test_default_prints_cron() {
  out=$(run_install)
  assert_contains "cortex cron snippet" "$out"
  assert_contains "lint.sh" "$out"
  assert_contains "fold.sh" "$out"
  assert_contains "dashboard.sh" "$out"
}

test_launchd_prints_plist() {
  out=$(run_install launchd)
  assert_contains "launchd" "$out"
  assert_contains "<plist" "$out"
}

test_gha_prints_yaml() {
  out=$(run_install gha)
  # GHA section emits a workflow snippet — should mention some recognizable token
  # The script outputs the GHA workflow header
  if [[ "$out" == *"GitHub Actions"* ]] || [[ "$out" == *"name:"* ]] || [[ "$out" == *"workflow"* ]]; then
    _TESTS_RUN=$((_TESTS_RUN + 1))
  else
    _TESTS_FAIL=$((_TESTS_FAIL + 1))
    _TESTS_RUN=$((_TESTS_RUN + 1))
    printf '  FAIL: gha output has no recognizable token: %s\n' "${out:0:200}"
  fi
}

test_unknown_kind_exits_2() {
  CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" bash "$SCRIPT" totally-unknown >/dev/null 2>&1
  assert_eq "2" "$?"
}

test_includes_disclaimer() {
  out=$(run_install)
  assert_contains "本脚本仅打印" "$out"
}

run_test test_default_prints_cron     test_default_prints_cron
run_test test_launchd_prints_plist    test_launchd_prints_plist
run_test test_gha_prints_yaml         test_gha_prints_yaml
run_test test_unknown_kind_exits_2    test_unknown_kind_exits_2
run_test test_includes_disclaimer     test_includes_disclaimer

print_summary
