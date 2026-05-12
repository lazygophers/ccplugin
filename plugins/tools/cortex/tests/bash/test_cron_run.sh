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

# Per PRD: run.sh is env-free for config vars (vault/lang/settings/timeout/dry-run);
# tests now use --vault / --settings / --dry-run CLI flags or write ~/.cortex/config.json.
make_home_with_vault() {
  # make_home_with_vault <home> <vault> [extra-json-fields]
  local home="$1" vault="$2"
  mkdir -p "$home/.cortex"
  printf '{"vault":"%s"}\n' "$vault" > "$home/.cortex/config.json"
}

run_runsh() {
  local fakebin="$1" job="$2" prompt="$3"; shift 3
  local home; home=$(mktemp -d)
  local vault; vault=$(mktemp -d)
  make_home_with_vault "$home" "$vault"
  PATH="$fakebin:$PATH" \
    HOME="$home" \
    bash "$RUN_SH" "$job" --settings /dev/null -- "$prompt" "$@" 2>&1
}

test_dry_run_prints_command() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin"
  out=$(PATH="$sandbox/bin:$PATH" \
    HOME="$(mktemp -d)" \
    bash "$RUN_SH" lint --vault "$sandbox/v" --dry-run -- "test prompt")
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
  mkdir -p "$sandbox/h"
  make_home_with_vault "$sandbox/h" "$sandbox/v"
  PATH="$sandbox/bin:$PATH" HOME="$sandbox/h" \
    bash "$RUN_SH" myjob --settings /dev/null -- "do something" >/dev/null 2>&1
  assert_eq "0" "$?" "success path → exit 0"
  result_file="$sandbox/h/.cache/cortex/cron/myjob-$(date +%F).json"
  assert_file_exists "$result_file"
}

test_error_result_returns_1() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin" error
  mkdir -p "$sandbox/h"
  make_home_with_vault "$sandbox/h" "$sandbox/v"
  PATH="$sandbox/bin:$PATH" HOME="$sandbox/h" \
    bash "$RUN_SH" myjob --settings /dev/null -- "x" >/dev/null 2>&1
  assert_eq "1" "$?" "is_error=true → exit 1"
}

test_empty_output_returns_1() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin" empty
  mkdir -p "$sandbox/h"
  make_home_with_vault "$sandbox/h" "$sandbox/v"
  PATH="$sandbox/bin:$PATH" HOME="$sandbox/h" \
    bash "$RUN_SH" myjob --settings /dev/null -- "x" >/dev/null 2>&1
  assert_eq "1" "$?" "no result line → exit 1"
}

test_lock_busy_returns_2() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin" success
  local lock="/tmp/cortex-locktest-$$.lock"
  echo "$$" > "$lock"
  trap "rm -f '$lock'" RETURN
  if command -v flock >/dev/null 2>&1; then
    return 0
  fi
  mkdir -p "$sandbox/h"
  make_home_with_vault "$sandbox/h" "$sandbox/v"
  PATH="$sandbox/bin:$PATH" HOME="$sandbox/h" \
    bash "$RUN_SH" "locktest-$$" --settings /dev/null -- "x" >/dev/null 2>&1
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
  # No config, no --vault flag → exit 3.
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
  env -i PATH="$sandbox/bin:$PATH" HOME="$sandbox/h" \
    bash "$RUN_SH" myjob --dry-run -- "do x" >"$sandbox/out" 2>&1
  assert_eq "0" "$?"
  out=$(cat "$sandbox/out")
  assert_contains "$sandbox/v-from-config" "$out"
}

test_cli_flag_overrides_config_vault() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin" success
  mkdir -p "$sandbox/h/.cortex"
  cat > "$sandbox/h/.cortex/config.json" <<EOF
{ "vault": "$sandbox/v-from-config" }
EOF
  env -i PATH="$sandbox/bin:$PATH" HOME="$sandbox/h" \
    bash "$RUN_SH" myjob --vault "$sandbox/v-from-cli" --dry-run -- "do x" >"$sandbox/out" 2>&1
  assert_eq "0" "$?"
  out=$(cat "$sandbox/out")
  assert_contains "$sandbox/v-from-cli" "$out"
  assert_not_contains "v-from-config" "$out"
}

test_env_vault_ignored() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin" success
  # Per PRD: CORTEX_VAULT env is no longer consulted; expect exit 3.
  env -i PATH="$sandbox/bin:$PATH" HOME="$sandbox/h" \
    CORTEX_VAULT="$sandbox/v-from-env" \
    bash "$RUN_SH" myjob -- "x" >/dev/null 2>&1
  assert_eq "3" "$?" "env CORTEX_VAULT must not satisfy run.sh"
}

test_broken_config_fails_fast_in_runsh() {
  if ! command -v jq >/dev/null 2>&1; then
    return 0
  fi
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin" success
  mkdir -p "$sandbox/h/.cortex"
  printf '%s' '{ broken' > "$sandbox/h/.cortex/config.json"
  env -i PATH="$sandbox/bin:$PATH" HOME="$sandbox/h" \
    bash "$RUN_SH" myjob --vault "$sandbox/v" -- "x" >/dev/null 2>"$sandbox/err"
  rc=$?
  assert_eq "1" "$rc" "broken config.json → run.sh exits 1"
  err=$(cat "$sandbox/err")
  assert_contains "config syntax error" "$err"
}

test_obsidian_vault_env_ignored() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_fakebin "$sandbox/bin" success
  # Per PRD: OBSIDIAN_VAULT is no longer consulted by run.sh; expect exit 3.
  env -i PATH="$sandbox/bin:$PATH" HOME="$sandbox/h" \
    OBSIDIAN_VAULT="$sandbox/v-obsidian" \
    bash "$RUN_SH" myjob -- "x" >/dev/null 2>&1
  assert_eq "3" "$?" "OBSIDIAN_VAULT env must not satisfy run.sh"
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
run_test test_cli_flag_overrides_config_vault test_cli_flag_overrides_config_vault
run_test test_env_vault_ignored            test_env_vault_ignored
run_test test_obsidian_vault_env_ignored   test_obsidian_vault_env_ignored
run_test test_broken_config_fails_fast_in_runsh test_broken_config_fails_fast_in_runsh

print_summary
