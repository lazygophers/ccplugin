#!/usr/bin/env bash
# Tests for scripts/lib/config.sh — bash counterpart of cortex_config.py.
# Each test sandboxes $HOME so the real ~/.cortex/config.json is never touched.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/../.." && pwd)"
# shellcheck source=./_assert.sh
source "$DIR/_assert.sh"

CONFIG_SH="$PLUGIN_ROOT/scripts/lib/config.sh"

# Helper: run `cortex_config_resolve` in a subshell with isolated HOME/env.
# Args: <home> <key> <env_var> <fallback> [env-assignments...]
# Echoes resolved value; returns the subshell's exit code.
resolve_in() {
  local home="$1" key="$2" envvar="$3" fallback="$4"; shift 4
  # Use env -i to avoid leaking the outer CORTEX_*; preserve PATH so jq works.
  env -i HOME="$home" PATH="$PATH" "$@" \
    bash -c "source '$CONFIG_SH'; cortex_config_resolve '$key' '$envvar' '$fallback'"
}

test_absent_config_returns_fallback() {
  local home; home=$(make_tmpdir); trap "rm -rf '$home'" RETURN
  out=$(resolve_in "$home" vault CORTEX_VAULT "/fallback/path")
  assert_eq "/fallback/path" "$out"
}

test_config_provides_value() {
  local home; home=$(make_tmpdir); trap "rm -rf '$home'" RETURN
  mkdir -p "$home/.cortex"
  cat > "$home/.cortex/config.json" <<'EOF'
{ "vault": "/from/config", "lang": "en-US" }
EOF
  out=$(resolve_in "$home" vault CORTEX_VAULT "/fallback")
  assert_eq "/from/config" "$out"
  out=$(resolve_in "$home" lang CORTEX_LANG "zh-CN")
  assert_eq "en-US" "$out"
}

test_env_overrides_config() {
  local home; home=$(make_tmpdir); trap "rm -rf '$home'" RETURN
  mkdir -p "$home/.cortex"
  cat > "$home/.cortex/config.json" <<'EOF'
{ "vault": "/from/config" }
EOF
  out=$(resolve_in "$home" vault CORTEX_VAULT "/fallback" CORTEX_VAULT=/from/env)
  assert_eq "/from/env" "$out"
}

test_empty_env_falls_through_to_config() {
  local home; home=$(make_tmpdir); trap "rm -rf '$home'" RETURN
  mkdir -p "$home/.cortex"
  cat > "$home/.cortex/config.json" <<'EOF'
{ "vault": "/from/config" }
EOF
  out=$(resolve_in "$home" vault CORTEX_VAULT "/fallback" CORTEX_VAULT=)
  assert_eq "/from/config" "$out"
}

test_empty_config_value_falls_through_to_fallback() {
  local home; home=$(make_tmpdir); trap "rm -rf '$home'" RETURN
  mkdir -p "$home/.cortex"
  cat > "$home/.cortex/config.json" <<'EOF'
{ "vault": "" }
EOF
  out=$(resolve_in "$home" vault CORTEX_VAULT "/fallback")
  assert_eq "/fallback" "$out"
}

test_missing_key_falls_through_to_fallback() {
  local home; home=$(make_tmpdir); trap "rm -rf '$home'" RETURN
  mkdir -p "$home/.cortex"
  cat > "$home/.cortex/config.json" <<'EOF'
{ "lang": "zh-CN" }
EOF
  out=$(resolve_in "$home" vault CORTEX_VAULT "/fallback")
  assert_eq "/fallback" "$out"
}

test_broken_json_fails_fast() {
  if ! command -v jq >/dev/null 2>&1; then
    return 0  # silent fallback path; nothing to test
  fi
  local home; home=$(make_tmpdir); trap "rm -rf '$home'" RETURN
  mkdir -p "$home/.cortex"
  printf '%s' '{ this is not json' > "$home/.cortex/config.json"
  local stderr_file="$home/err"
  out=$(env -i HOME="$home" PATH="$PATH" bash -c \
    "source '$CONFIG_SH'; cortex_config_init; cortex_config_resolve vault CORTEX_VAULT '/fallback'" \
    2>"$stderr_file") || rc=$?
  rc=${rc:-0}
  assert_eq "1" "$rc" "broken JSON should exit 1"
  err=$(cat "$stderr_file")
  assert_contains "config syntax error" "$err"
}

test_broken_json_fails_fast_in_caller_when_resolve_in_subshell() {
  # Regression: ensure JSON validation propagates from caller, not from a $() subshell.
  if ! command -v jq >/dev/null 2>&1; then
    return 0
  fi
  local home; home=$(make_tmpdir); trap "rm -rf '$home'" RETURN
  mkdir -p "$home/.cortex"
  printf '%s' '{ broken' > "$home/.cortex/config.json"
  local stderr_file="$home/err"
  # Mirror real usage: VAULT="$(cortex_config_resolve ...)" with init beforehand.
  env -i HOME="$home" PATH="$PATH" bash -c \
    "set -uo pipefail
     source '$CONFIG_SH'
     cortex_config_init
     VAULT=\"\$(cortex_config_resolve vault CORTEX_VAULT '/fb')\"
     echo \"reached:\$VAULT\"" \
    >/dev/null 2>"$stderr_file" || rc=$?
  rc=${rc:-0}
  assert_eq "1" "$rc" "broken JSON via init must exit 1 from caller process"
  err=$(cat "$stderr_file")
  assert_contains "config syntax error" "$err"
}

test_non_object_root_fails_fast() {
  if ! command -v jq >/dev/null 2>&1; then
    return 0
  fi
  local home; home=$(make_tmpdir); trap "rm -rf '$home'" RETURN
  mkdir -p "$home/.cortex"
  printf '%s' '[1,2,3]' > "$home/.cortex/config.json"
  local stderr_file="$home/err"
  env -i HOME="$home" PATH="$PATH" bash -c \
    "source '$CONFIG_SH'; cortex_config_init; cortex_config_resolve vault CORTEX_VAULT '/fallback'" \
    >/dev/null 2>"$stderr_file" || rc=$?
  rc=${rc:-0}
  assert_eq "1" "$rc" "non-object root should exit 1"
  err=$(cat "$stderr_file")
  assert_contains "config syntax error" "$err"
}

run_test test_absent_config_returns_fallback           test_absent_config_returns_fallback
run_test test_config_provides_value                    test_config_provides_value
run_test test_env_overrides_config                     test_env_overrides_config
run_test test_empty_env_falls_through_to_config        test_empty_env_falls_through_to_config
run_test test_empty_config_value_falls_through_to_fallback test_empty_config_value_falls_through_to_fallback
run_test test_missing_key_falls_through_to_fallback    test_missing_key_falls_through_to_fallback
run_test test_broken_json_fails_fast                   test_broken_json_fails_fast
run_test test_broken_json_fails_fast_in_caller_when_resolve_in_subshell test_broken_json_fails_fast_in_caller_when_resolve_in_subshell
run_test test_non_object_root_fails_fast               test_non_object_root_fails_fast

print_summary
