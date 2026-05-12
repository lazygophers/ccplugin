#!/usr/bin/env bash
# Tests for scripts/install_wrappers.sh
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/../.." && pwd)"
# shellcheck source=./_assert.sh
source "$DIR/_assert.sh"

SCRIPT="$PLUGIN_ROOT/scripts/install_wrappers.sh"

WRAPPERS=(lint.sh fold.sh dashboard.sh doctor.sh install_cron.sh config.sh update.sh ingest.sh search.sh save.sh refactor.sh init.sh memory.sh recall.sh promote.sh consolidate.sh forget.sh)

test_missing_install_path_fails() {
  out=$(bash "$SCRIPT" 2>&1) && rc=$? || rc=$?
  assert_eq "2" "$rc"
  assert_contains "required" "$out"
}

test_nonexistent_install_path_fails() {
  out=$(bash "$SCRIPT" --install-path /definitely/does/not/exist 2>&1) && rc=$? || rc=$?
  assert_eq "3" "$rc"
}

test_generates_all_executable_wrappers() {
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
  # shell-only wrappers contain absolute install_path
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

test_skill_wrappers_invoke_slash_command() {
  # 新设计: skill wrappers 不再注入 SKILL.md, 而是调 /cortex:<name> slash command.
  # 行为由 commands/<name>.md 定义.
  local tgt; tgt=$(make_tmpdir); trap "rm -rf '$tgt'" RETURN
  bash "$SCRIPT" --install-path "$PLUGIN_ROOT" --target-dir "$tgt" >/dev/null 2>&1
  local w
  for w in ingest.sh search.sh save.sh refactor.sh; do
    out=$(cat "$tgt/$w")
    assert_contains "CORTEX_JOB_LABEL" "$out"
    local name="${w%.sh}"
    assert_contains "/cortex:$name" "$out"
  done
}

test_save_wrapper_is_no_args_slash_command() {
  # 新设计: save.sh 不接 stdin/args, 调 /cortex:save 处理 inbox 全部 (见 commands/save.md).
  local tgt; tgt=$(make_tmpdir); trap "rm -rf '$tgt'" RETURN
  bash "$SCRIPT" --install-path "$PLUGIN_ROOT" --target-dir "$tgt" >/dev/null 2>&1
  out=$(cat "$tgt/save.sh")
  assert_contains "/cortex:save" "$out"
  # 不应再含旧 stdin body 读取逻辑
  if echo "$out" | grep -q 'BODY="\$(cat)"'; then
    _TESTS_RUN=$((_TESTS_RUN + 1))
    _TESTS_FAIL=$((_TESTS_FAIL + 1))
    printf '  FAIL: save.sh should not read BODY from stdin in new design\n'
  fi
}

test_lint_wrapper_calls_slash_command() {
  # 新设计: lint.sh 调 /cortex:lint slash command. 真正的 lint.run python 调用
  # 由 commands/lint.md 内的 Bash 指令触发, 不在 wrapper 内.
  local tgt; tgt=$(make_tmpdir); trap "rm -rf '$tgt'" RETURN
  bash "$SCRIPT" --install-path "$PLUGIN_ROOT" --target-dir "$tgt" >/dev/null 2>&1
  out=$(cat "$tgt/lint.sh")
  assert_contains "/cortex:lint" "$out"
  assert_contains "cortex-lint" "$out"
}

test_all_generated_wrappers_pass_bash_n() {
  local tgt; tgt=$(make_tmpdir); trap "rm -rf '$tgt'" RETURN
  bash "$SCRIPT" --install-path "$PLUGIN_ROOT" --target-dir "$tgt" >/dev/null 2>&1
  local f
  for f in "$tgt"/*.sh; do
    if ! bash -n "$f" 2>/dev/null; then
      _TESTS_RUN=$((_TESTS_RUN + 1))
      _TESTS_FAIL=$((_TESTS_FAIL + 1))
      printf '  FAIL: bash -n failed for %s\n' "$(basename "$f")"
    else
      _TESTS_RUN=$((_TESTS_RUN + 1))
    fi
  done
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

test_slash_command_invocation_in_claude_wrappers() {
  # All claude-driven wrappers route through `claude -p "/cortex:<name>" --print`
  # (no --bare, no --allowed-tools, no args). AUTO_MODE markers live in
  # commands/<name>.md (loaded by the slash command), not in the wrapper.
  local tgt; tgt=$(make_tmpdir); trap "rm -rf '$tgt'" RETURN
  bash "$SCRIPT" --install-path "$PLUGIN_ROOT" --target-dir "$tgt" >/dev/null 2>&1
  local w
  for w in doctor.sh lint.sh ingest.sh search.sh save.sh refactor.sh \
           dashboard.sh fold.sh init.sh promote.sh forget.sh consolidate.sh \
           memory.sh recall.sh; do
    out=$(cat "$tgt/$w")
    local name="${w%.sh}"
    assert_contains "/cortex:$name" "$out"
    assert_contains "--print" "$out"
    # Must NOT carry legacy limit flags
    if echo "$out" | grep -qE '^[^#]*(--bare|--allowed-tools|--append-system-prompt)'; then
      _TESTS_RUN=$((_TESTS_RUN + 1))
      _TESTS_FAIL=$((_TESTS_FAIL + 1))
      printf '  FAIL: %s still contains legacy limit flags\n' "$w"
    fi
  done
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
run_test test_generates_all_executable_wrappers     test_generates_all_executable_wrappers
run_test test_wrappers_embed_absolute_install_path  test_wrappers_embed_absolute_install_path
run_test test_update_wrapper_contains_two_claude_commands test_update_wrapper_contains_two_claude_commands
run_test test_doctor_wrapper_guides_to_skill        test_doctor_wrapper_guides_to_skill
run_test test_skill_wrappers_invoke_slash_command   test_skill_wrappers_invoke_slash_command
run_test test_save_wrapper_is_no_args_slash_command test_save_wrapper_is_no_args_slash_command
run_test test_lint_wrapper_calls_slash_command      test_lint_wrapper_calls_slash_command
run_test test_all_generated_wrappers_pass_bash_n    test_all_generated_wrappers_pass_bash_n
run_test test_overwrite_default_warns_on_stderr     test_overwrite_default_warns_on_stderr
run_test test_no_overwrite_preserves_existing       test_no_overwrite_preserves_existing
run_test test_slash_command_invocation_in_claude_wrappers  test_slash_command_invocation_in_claude_wrappers
run_test test_shellcheck_clean                      test_shellcheck_clean

print_summary
