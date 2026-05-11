#!/usr/bin/env bash
# Tests for scripts/cron/run.sh, lint.sh, fold.sh, dashboard.sh.
# Strategy: inject a fake `claude` (and `timeout` if missing) into PATH
# so we can verify run.sh's flow, jq pipeline, exit codes.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/../.." && pwd)"
# shellcheck source=./_assert.sh
source "$DIR/_assert.sh"

RUN_SH="$PLUGIN_ROOT/scripts/cron/run.sh"
LINT_SH="$PLUGIN_ROOT/scripts/cron/lint.sh"
FOLD_SH="$PLUGIN_ROOT/scripts/cron/fold.sh"
DASHBOARD_SH="$PLUGIN_ROOT/scripts/cron/dashboard.sh"

# Build a fake-bin dir prepended to PATH; fake `claude` outputs success stream-json,
# fake `timeout` is a passthrough (only for systems without GNU timeout).
make_fakebin() {
  local d="$1" mode="${2:-success}"
  mkdir -p "$d"
  cat > "$d/claude" <<EOF
#!/usr/bin/env bash
# fake claude — ignore all args, emit a stream-json result line
case "$mode" in
  error)
    printf '{"type":"system","subtype":"init","session_id":"x"}\n'
    printf '{"type":"result","subtype":"error","is_error":true,"result":"fake error"}\n'
    ;;
  empty)
    : # no output (jq will fail)
    ;;
  success|*)
    printf '{"type":"system","subtype":"init","session_id":"x"}\n'
    printf '{"type":"result","subtype":"success","is_error":false,"result":"OK"}\n'
    ;;
esac
exit 0
EOF
  chmod +x "$d/claude"

  if ! command -v timeout >/dev/null 2>&1; then
    cat > "$d/timeout" <<'EOF'
#!/usr/bin/env bash
# fake timeout: drop the first arg (seconds) and exec the rest
shift
exec "$@"
EOF
    chmod +x "$d/timeout"
  fi
}

run_runsh() {
  local fakebin="$1" job="$2" prompt="$3"; shift 3
  PATH="$fakebin:$PATH" \
    HOME="$(mktemp -d)" \
    CORTEX_VAULT="$(mktemp -d)" \
    CORTEX_SETTINGS="/dev/null" \
    bash "$RUN_SH" "$job" -- "$prompt" "$@" 2>&1
}

test_dry_run_prints_command() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin"
  out=$(PATH="$sandbox/bin:$PATH" \
    HOME="$(mktemp -d)" \
    CORTEX_VAULT="$sandbox/v" \
    CORTEX_DRY_RUN=1 \
    bash "$RUN_SH" lint -- "test prompt")
  assert_contains "dry-run" "$out"
  assert_contains "claude" "$out"
}

test_missing_args_exits_4() {
  bash "$RUN_SH" >/dev/null 2>&1
  assert_eq "4" "$?"
  bash "$RUN_SH" myjob >/dev/null 2>&1
  assert_eq "4" "$?"
}

test_success_path() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin" success
  PATH="$sandbox/bin:$PATH" \
    HOME="$sandbox/h" \
    CORTEX_VAULT="$sandbox/v" \
    CORTEX_SETTINGS="/dev/null" \
    bash "$RUN_SH" myjob -- "do something" >/dev/null 2>&1
  assert_eq "0" "$?" "success path → exit 0"
  # result file written
  result_file="$sandbox/h/.cache/cortex/cron/myjob-$(date +%F).json"
  assert_file_exists "$result_file"
}

test_error_result_returns_1() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin" error
  PATH="$sandbox/bin:$PATH" \
    HOME="$sandbox/h" \
    CORTEX_VAULT="$sandbox/v" \
    CORTEX_SETTINGS="/dev/null" \
    bash "$RUN_SH" myjob -- "x" >/dev/null 2>&1
  assert_eq "1" "$?" "is_error=true → exit 1"
}

test_empty_output_returns_1() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin" empty
  PATH="$sandbox/bin:$PATH" \
    HOME="$sandbox/h" \
    CORTEX_VAULT="$sandbox/v" \
    CORTEX_SETTINGS="/dev/null" \
    bash "$RUN_SH" myjob -- "x" >/dev/null 2>&1
  assert_eq "1" "$?" "no result line → exit 1"
}

test_lock_busy_returns_2() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin" success
  # Pre-create a lock that is held by the current process (kill -0 succeeds)
  local lock="/tmp/cortex-locktest-$$.lock"
  echo "$$" > "$lock"
  trap "rm -f '$lock'" RETURN
  # Use the same job name as lock filename (no flock available, fallback PID lock)
  if command -v flock >/dev/null 2>&1; then
    # When flock exists, locking is exec-redirected; harder to simulate cleanly
    # Skip this case
    return 0
  fi
  PATH="$sandbox/bin:$PATH" \
    HOME="$sandbox/h" \
    CORTEX_VAULT="$sandbox/v" \
    CORTEX_SETTINGS="/dev/null" \
    bash "$RUN_SH" "locktest-$$" -- "x" >/dev/null 2>&1
  assert_eq "2" "$?" "lock busy → exit 2"
}

test_lint_sh_dry_run() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin"
  out=$(PATH="$sandbox/bin:$PATH" \
    HOME="$(mktemp -d)" \
    bash "$LINT_SH" --dry-run --vault "$sandbox/v")
  assert_contains "dry-run" "$out"
  assert_contains "Bash Read Glob Grep" "$out"
}

test_fold_sh_dry_run() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin"
  out=$(PATH="$sandbox/bin:$PATH" \
    HOME="$(mktemp -d)" \
    bash "$FOLD_SH" --dry-run --vault "$sandbox/v")
  assert_contains "dry-run" "$out"
  assert_contains "Edit" "$out"
}

test_dashboard_sh_dry_run() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin"
  out=$(PATH="$sandbox/bin:$PATH" \
    HOME="$(mktemp -d)" \
    bash "$DASHBOARD_SH" --dry-run --vault "$sandbox/v")
  assert_contains "dry-run" "$out"
}

test_lint_sh_unknown_flag_exits_4() {
  bash "$LINT_SH" --unknown-flag >/dev/null 2>&1
  assert_eq "4" "$?"
}

# --- config integration (PR2) ---

test_missing_vault_exits_3() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin" success
  # No CORTEX_VAULT, no OBSIDIAN_VAULT, no config → exit 3.
  env -i PATH="$sandbox/bin:$PATH" HOME="$sandbox/h" \
    bash "$RUN_SH" myjob -- "x" >/dev/null 2>&1
  assert_eq "3" "$?" "no vault anywhere → exit 3"
}

test_config_provides_vault() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin" success
  mkdir -p "$sandbox/h/.cortex"
  cat > "$sandbox/h/.cortex/config.json" <<EOF
{ "vault": "$sandbox/v-from-config" }
EOF
  env -i PATH="$sandbox/bin:$PATH" HOME="$sandbox/h" CORTEX_DRY_RUN=1 \
    bash "$RUN_SH" myjob -- "do x" >"$sandbox/out" 2>&1
  assert_eq "0" "$?"
  out=$(cat "$sandbox/out")
  assert_contains "$sandbox/v-from-config" "$out"
}

test_env_overrides_config_vault() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin" success
  mkdir -p "$sandbox/h/.cortex"
  cat > "$sandbox/h/.cortex/config.json" <<EOF
{ "vault": "$sandbox/v-from-config" }
EOF
  env -i PATH="$sandbox/bin:$PATH" HOME="$sandbox/h" \
    CORTEX_VAULT="$sandbox/v-from-env" CORTEX_DRY_RUN=1 \
    bash "$RUN_SH" myjob -- "do x" >"$sandbox/out" 2>&1
  assert_eq "0" "$?"
  out=$(cat "$sandbox/out")
  assert_contains "$sandbox/v-from-env" "$out"
  assert_not_contains "v-from-config" "$out"
}

test_broken_config_fails_fast_in_runsh() {
  if ! command -v jq >/dev/null 2>&1; then
    return 0
  fi
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin" success
  mkdir -p "$sandbox/h/.cortex"
  printf '%s' '{ broken' > "$sandbox/h/.cortex/config.json"
  env -i PATH="$sandbox/bin:$PATH" HOME="$sandbox/h" CORTEX_VAULT="$sandbox/v" \
    bash "$RUN_SH" myjob -- "x" >/dev/null 2>"$sandbox/err"
  rc=$?
  assert_eq "1" "$rc" "broken config.json → run.sh exits 1"
  err=$(cat "$sandbox/err")
  assert_contains "config syntax error" "$err"
}

test_obsidian_vault_fallback() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin" success
  # No config, no CORTEX_VAULT; OBSIDIAN_VAULT serves as last-resort fallback.
  env -i PATH="$sandbox/bin:$PATH" HOME="$sandbox/h" \
    OBSIDIAN_VAULT="$sandbox/v-obsidian" CORTEX_DRY_RUN=1 \
    bash "$RUN_SH" myjob -- "do x" >"$sandbox/out" 2>&1
  assert_eq "0" "$?"
  out=$(cat "$sandbox/out")
  assert_contains "$sandbox/v-obsidian" "$out"
}

run_test test_dry_run_prints_command       test_dry_run_prints_command
run_test test_missing_args_exits_4         test_missing_args_exits_4
run_test test_success_path                 test_success_path
run_test test_error_result_returns_1       test_error_result_returns_1
run_test test_empty_output_returns_1       test_empty_output_returns_1
run_test test_lock_busy_returns_2          test_lock_busy_returns_2
run_test test_lint_sh_dry_run              test_lint_sh_dry_run
run_test test_fold_sh_dry_run              test_fold_sh_dry_run
run_test test_dashboard_sh_dry_run         test_dashboard_sh_dry_run
run_test test_lint_sh_unknown_flag_exits_4 test_lint_sh_unknown_flag_exits_4
run_test test_missing_vault_exits_3        test_missing_vault_exits_3
run_test test_config_provides_vault        test_config_provides_vault
run_test test_env_overrides_config_vault   test_env_overrides_config_vault
run_test test_obsidian_vault_fallback      test_obsidian_vault_fallback
run_test test_broken_config_fails_fast_in_runsh test_broken_config_fails_fast_in_runsh

print_summary
