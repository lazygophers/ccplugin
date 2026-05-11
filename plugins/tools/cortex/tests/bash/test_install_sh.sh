#!/usr/bin/env bash
# Tests for install.sh (plugin-root 一键安装入口).
# 每个用例隔离 HOME, 不污染真实 ~/.cortex.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/../.." && pwd)"
# shellcheck source=./_assert.sh
source "$DIR/_assert.sh"

INSTALL_SH="$PLUGIN_ROOT/install.sh"

# 包装: 用 env -i 清环境, 显式给 HOME / PATH, 跑 install.sh
run_install() {
  local home="$1"; shift
  env -i HOME="$home" PATH="$PATH" bash "$INSTALL_SH" "$@"
}

test_help_prints_usage() {
  out=$(bash "$INSTALL_SH" --help 2>&1) && rc=$? || rc=$?
  assert_eq "0" "$rc"
  assert_contains "USAGE" "$out"
  assert_contains "--non-interactive" "$out"
}

test_unknown_flag_exits_2() {
  out=$(bash "$INSTALL_SH" --bogus 2>&1) && rc=$? || rc=$?
  assert_eq "2" "$rc"
  assert_contains "unknown" "$out"
}

test_non_interactive_missing_vault_exits_2() {
  local home; home=$(make_tmpdir); trap "rm -rf '$home'" RETURN
  out=$(run_install "$home" --non-interactive --use-source --no-cron 2>&1) && rc=$? || rc=$?
  assert_eq "2" "$rc"
  assert_contains "vault" "$out"
}

test_non_interactive_full_run_writes_config_and_wrappers() {
  local home; home=$(make_tmpdir); trap "rm -rf '$home'" RETURN
  local vault; vault=$(make_tmpdir)
  local settings="$home/settings.json"
  echo '{}' > "$settings"

  out=$(run_install "$home" \
    --non-interactive \
    --use-source \
    --vault "$vault" \
    --lang en-US \
    --settings "$settings" \
    --no-cron 2>&1) && rc=$? || rc=$?

  assert_eq "0" "$rc"
  assert_file_exists "$home/.cortex/config.json"
  # config 字段写入正确
  assert_contains "\"vault\": \"$vault\"" "$(cat "$home/.cortex/config.json")"
  assert_contains "\"lang\": \"en-US\"" "$(cat "$home/.cortex/config.json")"
  assert_contains "\"settings\": \"$settings\"" "$(cat "$home/.cortex/config.json")"
  assert_contains "\"install_path\": \"$PLUGIN_ROOT\"" "$(cat "$home/.cortex/config.json")"

  # 七件套全部生成可执行
  local wrappers=(lint.sh fold.sh dashboard.sh doctor.sh install_cron.sh config.sh update.sh)
  local w
  for w in "${wrappers[@]}"; do
    if [[ ! -x "$home/.cortex/scripts/$w" ]]; then
      _TESTS_RUN=$((_TESTS_RUN + 1))
      _TESTS_FAIL=$((_TESTS_FAIL + 1))
      printf '  FAIL: wrapper missing or not executable: %s\n' "$w"
    fi
  done

  # next-step 提示
  assert_contains "cortex 安装完成" "$out"
  assert_contains "doctor.sh" "$out"
}

test_idempotent_second_run_overwrites() {
  local home; home=$(make_tmpdir); trap "rm -rf '$home'" RETURN
  local vault1; vault1=$(make_tmpdir)
  local vault2; vault2=$(make_tmpdir)

  run_install "$home" --non-interactive --use-source --vault "$vault1" --no-cron >/dev/null 2>&1
  out=$(run_install "$home" --non-interactive --use-source --vault "$vault2" --no-cron 2>&1) && rc=$? || rc=$?

  assert_eq "0" "$rc"
  assert_contains "\"vault\": \"$vault2\"" "$(cat "$home/.cortex/config.json")"
}

test_install_path_via_env() {
  local home; home=$(make_tmpdir); trap "rm -rf '$home'" RETURN
  local vault; vault=$(make_tmpdir)
  out=$(env -i HOME="$home" PATH="$PATH" CORTEX_INSTALL_PATH="$PLUGIN_ROOT" \
    bash "$INSTALL_SH" --non-interactive --vault "$vault" --no-cron 2>&1) && rc=$? || rc=$?
  assert_eq "0" "$rc"
  assert_contains "\"install_path\": \"$PLUGIN_ROOT\"" "$(cat "$home/.cortex/config.json")"
}

test_invalid_install_path_exits_2() {
  out=$(env -i HOME="$(mktemp -d)" PATH="$PATH" CORTEX_INSTALL_PATH=/definitely/not/here \
    bash "$INSTALL_SH" --non-interactive --vault /tmp 2>&1) && rc=$? || rc=$?
  assert_eq "2" "$rc"
}

test_shellcheck_clean() {
  if ! command -v shellcheck >/dev/null 2>&1; then
    _TESTS_RUN=$((_TESTS_RUN + 1))
    printf '  SKIP: shellcheck not installed\n'
    return 0
  fi
  if shellcheck "$INSTALL_SH" >/dev/null 2>&1; then
    _TESTS_RUN=$((_TESTS_RUN + 1))
  else
    _TESTS_RUN=$((_TESTS_RUN + 1))
    _TESTS_FAIL=$((_TESTS_FAIL + 1))
    printf '  FAIL: shellcheck reported issues in %s\n' "$INSTALL_SH"
    shellcheck "$INSTALL_SH" || true
  fi
}

run_test test_help_prints_usage                          test_help_prints_usage
run_test test_unknown_flag_exits_2                       test_unknown_flag_exits_2
run_test test_non_interactive_missing_vault_exits_2      test_non_interactive_missing_vault_exits_2
run_test test_non_interactive_full_run_writes_config_and_wrappers \
                                                          test_non_interactive_full_run_writes_config_and_wrappers
run_test test_idempotent_second_run_overwrites           test_idempotent_second_run_overwrites
run_test test_install_path_via_env                       test_install_path_via_env
run_test test_invalid_install_path_exits_2               test_invalid_install_path_exits_2
run_test test_shellcheck_clean                           test_shellcheck_clean

print_summary
