#!/usr/bin/env bash
# Tests for scripts/install_wrappers.sh
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/../.." && pwd)"
# shellcheck source=./_assert.sh
source "$DIR/_assert.sh"

SCRIPT="$PLUGIN_ROOT/scripts/install_wrappers.sh"

WRAPPERS=(lint.sh fold.sh dashboard.sh doctor.sh install_cron.sh config.sh update.sh)

test_missing_install_path_fails() {
  out=$(bash "$SCRIPT" 2>&1) && rc=$? || rc=$?
  assert_eq "2" "$rc"
  assert_contains "required" "$out"
}

test_nonexistent_install_path_fails() {
  out=$(bash "$SCRIPT" --install-path /definitely/does/not/exist 2>&1) && rc=$? || rc=$?
  assert_eq "3" "$rc"
}

test_generates_seven_executable_wrappers() {
  local tgt; tgt=$(make_tmpdir); trap "rm -rf '$tgt'" RETURN
  bash "$SCRIPT" --install-path "$PLUGIN_ROOT" --target-dir "$tgt" >/dev/null 2>&1
  local f
  for f in "${WRAPPERS[@]}"; do
    if [[ ! -f "$tgt/$f" ]]; then
      _TESTS_RUN=$((_TESTS_RUN + 1))
      _TESTS_FAIL=$((_TESTS_FAIL + 1))
      printf '  FAIL: missing wrapper %s\n' "$f"
      continue
    fi
    if [[ ! -x "$tgt/$f" ]]; then
      _TESTS_RUN=$((_TESTS_RUN + 1))
      _TESTS_FAIL=$((_TESTS_FAIL + 1))
      printf '  FAIL: wrapper not executable: %s\n' "$f"
      continue
    fi
    # shebang
    local first; first=$(head -n1 "$tgt/$f")
    assert_eq "#!/usr/bin/env bash" "$first"
  done
}

test_wrappers_embed_absolute_install_path() {
  local tgt; tgt=$(make_tmpdir); trap "rm -rf '$tgt'" RETURN
  bash "$SCRIPT" --install-path "$PLUGIN_ROOT" --target-dir "$tgt" >/dev/null 2>&1
  # cron wrappers contain the full path
  out=$(cat "$tgt/lint.sh")
  assert_contains "$PLUGIN_ROOT/scripts/cron/lint.sh" "$out"
  out=$(cat "$tgt/fold.sh")
  assert_contains "$PLUGIN_ROOT/scripts/cron/fold.sh" "$out"
  out=$(cat "$tgt/dashboard.sh")
  assert_contains "$PLUGIN_ROOT/scripts/cron/dashboard.sh" "$out"
  out=$(cat "$tgt/install_cron.sh")
  assert_contains "$PLUGIN_ROOT/scripts/install_cron.sh" "$out"
  out=$(cat "$tgt/config.sh")
  assert_contains "$PLUGIN_ROOT/scripts/cortex_config.py" "$out"
}

test_update_wrapper_contains_two_claude_commands() {
  local tgt; tgt=$(make_tmpdir); trap "rm -rf '$tgt'" RETURN
  bash "$SCRIPT" --install-path "$PLUGIN_ROOT" --target-dir "$tgt" >/dev/null 2>&1
  out=$(cat "$tgt/update.sh")
  assert_contains "claude plugins marketplace update ccplugin-market" "$out"
  assert_contains "claude plugins update cortex@ccplugin-market" "$out"
}

test_doctor_wrapper_guides_to_skill() {
  local tgt; tgt=$(make_tmpdir); trap "rm -rf '$tgt'" RETURN
  bash "$SCRIPT" --install-path "$PLUGIN_ROOT" --target-dir "$tgt" >/dev/null 2>&1
  out=$(cat "$tgt/doctor.sh")
  assert_contains "cortex-doctor" "$out"
}

test_overwrite_default_warns_on_stderr() {
  local tgt; tgt=$(make_tmpdir); trap "rm -rf '$tgt'" RETURN
  bash "$SCRIPT" --install-path "$PLUGIN_ROOT" --target-dir "$tgt" >/dev/null 2>&1
  # second run: existing files trigger "regenerated" stderr lines
  err=$(bash "$SCRIPT" --install-path "$PLUGIN_ROOT" --target-dir "$tgt" 2>&1 >/dev/null)
  assert_contains "regenerated" "$err"
}

test_no_overwrite_preserves_existing() {
  local tgt; tgt=$(make_tmpdir); trap "rm -rf '$tgt'" RETURN
  mkdir -p "$tgt"
  echo 'sentinel' > "$tgt/lint.sh"
  chmod +x "$tgt/lint.sh"
  err=$(bash "$SCRIPT" --install-path "$PLUGIN_ROOT" --target-dir "$tgt" --no-overwrite 2>&1 >/dev/null)
  assert_contains "skipped" "$err"
  out=$(cat "$tgt/lint.sh")
  assert_eq "sentinel" "$out"
  # other wrappers should still be written
  if [[ ! -f "$tgt/fold.sh" ]]; then
    _TESTS_RUN=$((_TESTS_RUN + 1))
    _TESTS_FAIL=$((_TESTS_FAIL + 1))
    printf '  FAIL: --no-overwrite should still create absent wrappers\n'
  fi
}

test_shellcheck_clean() {
  if ! command -v shellcheck >/dev/null 2>&1; then
    _TESTS_RUN=$((_TESTS_RUN + 1))
    printf '  SKIP: shellcheck not installed\n'
    return 0
  fi
  if shellcheck "$SCRIPT" >/dev/null 2>&1; then
    _TESTS_RUN=$((_TESTS_RUN + 1))
  else
    _TESTS_RUN=$((_TESTS_RUN + 1))
    _TESTS_FAIL=$((_TESTS_FAIL + 1))
    printf '  FAIL: shellcheck reported issues in %s\n' "$SCRIPT"
    shellcheck "$SCRIPT" || true
  fi
}

run_test test_missing_install_path_fails            test_missing_install_path_fails
run_test test_nonexistent_install_path_fails        test_nonexistent_install_path_fails
run_test test_generates_seven_executable_wrappers   test_generates_seven_executable_wrappers
run_test test_wrappers_embed_absolute_install_path  test_wrappers_embed_absolute_install_path
run_test test_update_wrapper_contains_two_claude_commands test_update_wrapper_contains_two_claude_commands
run_test test_doctor_wrapper_guides_to_skill        test_doctor_wrapper_guides_to_skill
run_test test_overwrite_default_warns_on_stderr     test_overwrite_default_warns_on_stderr
run_test test_no_overwrite_preserves_existing       test_no_overwrite_preserves_existing
run_test test_shellcheck_clean                      test_shellcheck_clean

print_summary
