#!/usr/bin/env bash
# Tests for scripts/install_cron.sh
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/../.." && pwd)"
# shellcheck source=./_assert.sh
source "$DIR/_assert.sh"

SCRIPT="$PLUGIN_ROOT/scripts/install_cron.sh"

# 默认隔离: 清空可能影响解析优先级的环境变量, 走 --plugin-root 注入。
# Provide a CORTEX_VAULT so install_cron.sh's hard-fail (no vault) doesn't trip
# tests that don't care about vault resolution.
run_install() {
  env -u CLAUDE_PLUGIN_ROOT -u CORTEX_INSTALL_PATH \
    CORTEX_VAULT="/tmp/test-vault" \
    bash "$SCRIPT" --plugin-root "$PLUGIN_ROOT" "$@" 2>&1
}

run_install_raw() {
  CORTEX_VAULT="/tmp/test-vault" bash "$SCRIPT" "$@"
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
  if [[ "$out" == *"GitHub Actions"* ]] || [[ "$out" == *"name:"* ]] || [[ "$out" == *"workflow"* ]]; then
    _TESTS_RUN=$((_TESTS_RUN + 1))
  else
    _TESTS_FAIL=$((_TESTS_FAIL + 1))
    _TESTS_RUN=$((_TESTS_RUN + 1))
    printf '  FAIL: gha output has no recognizable token: %s\n' "${out:0:200}"
  fi
}

test_unknown_kind_exits_2() {
  env -u CLAUDE_PLUGIN_ROOT -u CORTEX_INSTALL_PATH \
    CORTEX_VAULT="/tmp/test-vault" \
    bash "$SCRIPT" totally-unknown >/dev/null 2>&1
  assert_eq "2" "$?"
}

test_includes_disclaimer() {
  out=$(run_install)
  assert_contains "本脚本仅打印" "$out"
}

# ---- 新增: PLUGIN_ROOT 解析优先级 ----

test_help_lists_six_precedences() {
  out=$(run_install_raw --help 2>&1)
  assert_contains "1. --plugin-root" "$out"
  assert_contains "2. \$CORTEX_INSTALL_PATH" "$out"
  assert_contains "marketplaces/ccplugin-market" "$out"
  assert_contains "5. \$CLAUDE_PLUGIN_ROOT" "$out"
  assert_contains "6. fallback" "$out"
}

test_plugin_root_flag_overrides() {
  out=$(env -u CLAUDE_PLUGIN_ROOT -u CORTEX_INSTALL_PATH \
    CORTEX_VAULT="/tmp/test-vault" \
    bash "$SCRIPT" --plugin-root /custom/path 2>&1)
  assert_contains "/custom/path/scripts/cron/lint.sh" "$out"
  assert_contains "PLUGIN_ROOT = /custom/path" "$out"
}

test_cortex_install_path_env_overrides() {
  out=$(env -u CLAUDE_PLUGIN_ROOT \
    CORTEX_INSTALL_PATH=/env/override \
    CORTEX_VAULT="/tmp/test-vault" \
    bash "$SCRIPT" 2>&1)
  assert_contains "/env/override/scripts/cron/lint.sh" "$out"
}

test_default_marketplace_path_when_exists() {
  # mock 一个 fake HOME, 创建主 marketplace 目录
  local fake_home
  fake_home="$(mktemp -d)"
  local mp="$fake_home/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex"
  mkdir -p "$mp"
  out=$(env -u CLAUDE_PLUGIN_ROOT -u CORTEX_INSTALL_PATH \
    HOME="$fake_home" CORTEX_VAULT="/tmp/test-vault" bash "$SCRIPT" 2>&1)
  assert_contains "$mp/scripts/cron/lint.sh" "$out"
  rm -rf "$fake_home"
}

test_xdg_marketplace_fallback() {
  local fake_home
  fake_home="$(mktemp -d)"
  local mp="$fake_home/.config/claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex"
  mkdir -p "$mp"
  out=$(env -u CLAUDE_PLUGIN_ROOT -u CORTEX_INSTALL_PATH \
    HOME="$fake_home" CORTEX_VAULT="/tmp/test-vault" bash "$SCRIPT" 2>&1)
  assert_contains "$mp/scripts/cron/lint.sh" "$out"
  rm -rf "$fake_home"
}

test_fallback_warns_when_marketplace_absent() {
  local fake_home
  fake_home="$(mktemp -d)"
  out=$(env -u CLAUDE_PLUGIN_ROOT -u CORTEX_INSTALL_PATH \
    HOME="$fake_home" CORTEX_VAULT="/tmp/test-vault" bash "$SCRIPT" 2>&1)
  assert_contains "WARNING" "$out"
  assert_contains "未检测到 marketplace" "$out"
  # 仍输出 snippet
  assert_contains "cortex cron snippet" "$out"
  rm -rf "$fake_home"
}

test_snippet_contains_no_variable_placeholder() {
  # cron snippet 中 PLUGIN_ROOT 应已被替换为绝对路径字符串, 不含 ${PLUGIN_ROOT} 占位
  out=$(run_install)
  # cron 段的 lint.sh 行不应该带 '${PLUGIN_ROOT}' 字面量
  cron_lines=$(printf '%s\n' "$out" | grep -E 'cron/(lint|fold|dashboard)\.sh' || true)
  if [[ -n "$cron_lines" ]] && [[ "$cron_lines" == *'${PLUGIN_ROOT}'* ]]; then
    _TESTS_RUN=$((_TESTS_RUN + 1))
    _TESTS_FAIL=$((_TESTS_FAIL + 1))
    printf '  FAIL: cron snippet still contains \${PLUGIN_ROOT} placeholder: %s\n' "$cron_lines"
  else
    _TESTS_RUN=$((_TESTS_RUN + 1))
  fi
  # launchd 同样
  out2=$(run_install launchd)
  launchd_lines=$(printf '%s\n' "$out2" | grep -E 'cron/(lint|fold|dashboard)\.sh' || true)
  if [[ -n "$launchd_lines" ]] && [[ "$launchd_lines" == *'${PLUGIN_ROOT}'* ]]; then
    _TESTS_RUN=$((_TESTS_RUN + 1))
    _TESTS_FAIL=$((_TESTS_FAIL + 1))
    printf '  FAIL: launchd snippet still contains \${PLUGIN_ROOT} placeholder\n'
  else
    _TESTS_RUN=$((_TESTS_RUN + 1))
  fi
}

run_test test_default_prints_cron                test_default_prints_cron
run_test test_launchd_prints_plist               test_launchd_prints_plist
run_test test_gha_prints_yaml                    test_gha_prints_yaml
run_test test_unknown_kind_exits_2               test_unknown_kind_exits_2
run_test test_includes_disclaimer                test_includes_disclaimer
run_test test_help_lists_six_precedences         test_help_lists_six_precedences
run_test test_plugin_root_flag_overrides         test_plugin_root_flag_overrides
run_test test_cortex_install_path_env_overrides  test_cortex_install_path_env_overrides
run_test test_default_marketplace_path_when_exists test_default_marketplace_path_when_exists
run_test test_xdg_marketplace_fallback           test_xdg_marketplace_fallback
run_test test_fallback_warns_when_marketplace_absent test_fallback_warns_when_marketplace_absent
run_test test_snippet_contains_no_variable_placeholder test_snippet_contains_no_variable_placeholder

print_summary
