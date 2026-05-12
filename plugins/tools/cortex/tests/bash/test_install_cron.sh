#!/usr/bin/env bash
# Tests for scripts/install_cron.sh
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/../.." && pwd)"
# shellcheck source=./_assert.sh
source "$DIR/_assert.sh"

SCRIPT="$PLUGIN_ROOT/scripts/install_cron.sh"

# Per PRD: install_cron.sh is env-free for config (vault/install_path); tests
# provide a mock ~/.cortex/config.json via HOME override.
make_test_home() {
  local home; home=$(mktemp -d)
  mkdir -p "$home/.cortex"
  printf '{"vault":"/tmp/test-vault"}\n' > "$home/.cortex/config.json"
  printf '%s' "$home"
}

# 默认隔离: 清空可能影响解析优先级的环境变量, 走 --plugin-root 注入。
run_install() {
  local home; home=$(make_test_home)
  env -u CLAUDE_PLUGIN_ROOT \
    HOME="$home" \
    bash "$SCRIPT" --plugin-root "$PLUGIN_ROOT" "$@" 2>&1
  rm -rf "$home"
}

run_install_raw() {
  local home; home=$(make_test_home)
  HOME="$home" bash "$SCRIPT" "$@"
  rm -rf "$home"
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
  local home; home=$(make_test_home)
  env -u CLAUDE_PLUGIN_ROOT \
    HOME="$home" \
    bash "$SCRIPT" totally-unknown >/dev/null 2>&1
  assert_eq "2" "$?"
  rm -rf "$home"
}

test_includes_disclaimer() {
  out=$(run_install)
  assert_contains "本脚本仅打印" "$out"
}

# ---- 新增: PLUGIN_ROOT 解析优先级 ----

setup_home_with_vault() {
  # setup_home_with_vault <home>
  mkdir -p "$1/.cortex"
  printf '{"vault":"/tmp/test-vault"}\n' > "$1/.cortex/config.json"
}

setup_home_with_install_path() {
  # setup_home_with_install_path <home> <install_path>
  mkdir -p "$1/.cortex"
  printf '{"vault":"/tmp/test-vault","install_path":"%s"}\n' "$2" > "$1/.cortex/config.json"
}

test_help_lists_six_precedences() {
  out=$(run_install_raw --help 2>&1)
  assert_contains "1. --plugin-root" "$out"
  assert_contains "2. ~/.cortex/config.json" "$out"
  assert_contains "marketplaces/ccplugin-market" "$out"
  assert_contains "5. \$CLAUDE_PLUGIN_ROOT" "$out"
  assert_contains "6. fallback" "$out"
}

test_plugin_root_flag_overrides() {
  local home; home=$(mktemp -d)
  setup_home_with_vault "$home"
  out=$(env -u CLAUDE_PLUGIN_ROOT \
    HOME="$home" \
    bash "$SCRIPT" --plugin-root /custom/path 2>&1)
  assert_contains "/custom/path/scripts/cron/lint.sh" "$out"
  assert_contains "PLUGIN_ROOT = /custom/path" "$out"
  rm -rf "$home"
}

test_config_install_path_overrides() {
  # Per PRD: install_path is now read from ~/.cortex/config.json (was CORTEX_INSTALL_PATH env).
  local home; home=$(mktemp -d)
  setup_home_with_install_path "$home" "/config/override"
  out=$(env -u CLAUDE_PLUGIN_ROOT \
    HOME="$home" \
    bash "$SCRIPT" 2>&1)
  assert_contains "/config/override/scripts/cron/lint.sh" "$out"
  rm -rf "$home"
}

test_default_marketplace_path_when_exists() {
  local fake_home
  fake_home="$(mktemp -d)"
  local mp="$fake_home/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex"
  mkdir -p "$mp"
  setup_home_with_vault "$fake_home"
  out=$(env -u CLAUDE_PLUGIN_ROOT \
    HOME="$fake_home" bash "$SCRIPT" 2>&1)
  assert_contains "$mp/scripts/cron/lint.sh" "$out"
  rm -rf "$fake_home"
}

test_xdg_marketplace_fallback() {
  local fake_home
  fake_home="$(mktemp -d)"
  local mp="$fake_home/.config/claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex"
  mkdir -p "$mp"
  setup_home_with_vault "$fake_home"
  out=$(env -u CLAUDE_PLUGIN_ROOT \
    HOME="$fake_home" bash "$SCRIPT" 2>&1)
  assert_contains "$mp/scripts/cron/lint.sh" "$out"
  rm -rf "$fake_home"
}

test_fallback_warns_when_marketplace_absent() {
  local fake_home
  fake_home="$(mktemp -d)"
  setup_home_with_vault "$fake_home"
  out=$(env -u CLAUDE_PLUGIN_ROOT \
    HOME="$fake_home" bash "$SCRIPT" 2>&1)
  assert_contains "WARNING" "$out"
  assert_contains "未检测到 marketplace" "$out"
  # 仍输出 snippet
  assert_contains "cortex cron snippet" "$out"
  rm -rf "$fake_home"
}

test_snippet_contains_no_variable_placeholder() {
  # cron snippet 中 PLUGIN_ROOT 应已被替换为绝对路径字符串, 不含 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex 占位
  out=$(run_install)
  # cron 段的 lint.sh 行不应该带 '~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex' 字面量
  cron_lines=$(printf '%s\n' "$out" | grep -E 'cron/(lint|fold|dashboard)\.sh' || true)
  if [[ -n "$cron_lines" ]] && [[ "$cron_lines" == *'~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex'* ]]; then
    _TESTS_RUN=$((_TESTS_RUN + 1))
    _TESTS_FAIL=$((_TESTS_FAIL + 1))
    printf '  FAIL: cron snippet still contains \~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex placeholder: %s\n' "$cron_lines"
  else
    _TESTS_RUN=$((_TESTS_RUN + 1))
  fi
  # launchd 同样
  out2=$(run_install launchd)
  launchd_lines=$(printf '%s\n' "$out2" | grep -E 'cron/(lint|fold|dashboard)\.sh' || true)
  if [[ -n "$launchd_lines" ]] && [[ "$launchd_lines" == *'~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex'* ]]; then
    _TESTS_RUN=$((_TESTS_RUN + 1))
    _TESTS_FAIL=$((_TESTS_FAIL + 1))
    printf '  FAIL: launchd snippet still contains \~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex placeholder\n'
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
run_test test_config_install_path_overrides     test_config_install_path_overrides
run_test test_default_marketplace_path_when_exists test_default_marketplace_path_when_exists
run_test test_xdg_marketplace_fallback           test_xdg_marketplace_fallback
run_test test_fallback_warns_when_marketplace_absent test_fallback_warns_when_marketplace_absent
run_test test_snippet_contains_no_variable_placeholder test_snippet_contains_no_variable_placeholder

print_summary
