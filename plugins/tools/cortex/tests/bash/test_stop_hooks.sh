#!/usr/bin/env bash
# Tests for hooks/stop.sh and hooks/post_compact.sh
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/../.." && pwd)"
# shellcheck source=./_assert.sh
source "$DIR/_assert.sh"

STOP="$PLUGIN_ROOT/hooks/stop.sh"
POST_COMPACT="$PLUGIN_ROOT/hooks/post_compact.sh"

make_vault() {
  local root="$1"
  mkdir -p "$root/.obsidian" "$root/_meta" "$root/log" "$root/folds"
  printf '{"lang":"zh-CN","preset":"lyt"}\n' > "$root/_meta/version.json"
  : > "$root/index.md"
}

make_transcript() {
  # $1=path, $2=trivial|nontrivial
  local p="$1" mode="$2"
  if [[ "$mode" == "nontrivial" ]]; then
    cat > "$p" <<'EOF'
{"type":"user","message":{"role":"user","content":"决策 修复"}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"src/a.py:10 lib/b.rs:42 mod/c.go:5\ndiff --git a/foo b/foo\n@@ -1,1 +1,1 @@"}]}}
EOF
  else
    cat > "$p" <<'EOF'
{"type":"user","message":{"role":"user","content":"hi"}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"hello"}]}}
EOF
  fi
}

run_stop() {
  # stdin = JSON; env vars = vault override
  local vault="$1" json="$2"
  printf '%s' "$json" | env -i PATH="$PATH" \
    CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" \
    OBSIDIAN_VAULT="$vault" \
    HOME="$(mktemp -d)" \
    bash "$STOP" 2>/dev/null
}

test_empty_stdin_silent() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_vault "$sandbox/v"
  out=$(run_stop "$sandbox/v" "")
  assert_empty "$out" "empty stdin → no output"
}

test_stop_active_skipped() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_vault "$sandbox/v"
  local tp="$sandbox/t.jsonl"
  make_transcript "$tp" nontrivial
  local payload
  payload=$(printf '{"transcript_path":"%s","stop_hook_active":true,"hook_event_name":"Stop","session_id":"s1"}' "$tp")
  out=$(run_stop "$sandbox/v" "$payload")
  assert_empty "$out" "stop_hook_active=true → no output"
}

test_trivial_no_save() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_vault "$sandbox/v"
  local tp="$sandbox/t.jsonl"
  make_transcript "$tp" trivial
  local payload
  payload=$(printf '{"transcript_path":"%s","stop_hook_active":false,"hook_event_name":"Stop","session_id":"s1"}' "$tp")
  out=$(run_stop "$sandbox/v" "$payload")
  assert_empty "$out" "trivial transcript → no save → no output"
  # log dir empty
  count=$(find "$sandbox/v/log" -type f -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
  assert_eq "0" "$count"
}

test_nontrivial_writes_log_and_outputs_json() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_vault "$sandbox/v"
  local tp="$sandbox/t.jsonl"
  make_transcript "$tp" nontrivial
  local payload
  payload=$(printf '{"transcript_path":"%s","stop_hook_active":false,"hook_event_name":"Stop","session_id":"s1"}' "$tp")
  out=$(run_stop "$sandbox/v" "$payload")
  assert_contains "hookSpecificOutput" "$out"
  assert_contains "已落档" "$out"
  count=$(find "$sandbox/v/log" -type f -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
  assert_neq "0" "$count" "expected log file written"
}

test_vault_missing_silent() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  local tp="$sandbox/t.jsonl"
  make_transcript "$tp" nontrivial
  local payload
  payload=$(printf '{"transcript_path":"%s","stop_hook_active":false,"hook_event_name":"Stop","session_id":"s"}' "$tp")
  out=$(printf '%s' "$payload" | env -i PATH="$PATH" \
    CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" \
    HOME="$sandbox/empty" \
    XDG_CONFIG_HOME="$sandbox/xdg" \
    bash "$STOP" 2>/dev/null)
  assert_empty "$out"
}

test_post_compact_force_writes() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_vault "$sandbox/v"
  local tp="$sandbox/t.jsonl"
  # Even trivial transcript triggers under compact (--force)
  make_transcript "$tp" trivial
  local payload
  payload=$(printf '{"transcript_path":"%s","session_id":"s1"}' "$tp")
  out=$(printf '%s' "$payload" | env -i PATH="$PATH" \
    CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" \
    OBSIDIAN_VAULT="$sandbox/v" \
    HOME="$(mktemp -d)" \
    bash "$POST_COMPACT" 2>/dev/null)
  assert_contains "PostCompact" "$out"
  count=$(find "$sandbox/v/log" -type f -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
  assert_neq "0" "$count"
}

test_post_compact_empty_stdin() {
  local sandbox; sandbox=$(make_tmpdir); trap "rm -rf '$sandbox'" RETURN
  make_vault "$sandbox/v"
  out=$(printf '' | env -i PATH="$PATH" \
    CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" \
    OBSIDIAN_VAULT="$sandbox/v" \
    HOME="$(mktemp -d)" \
    bash "$POST_COMPACT" 2>/dev/null)
  assert_empty "$out"
}

run_test test_empty_stdin_silent              test_empty_stdin_silent
run_test test_stop_active_skipped             test_stop_active_skipped
run_test test_trivial_no_save                 test_trivial_no_save
run_test test_nontrivial_writes_log_and_outputs_json  test_nontrivial_writes_log_and_outputs_json
run_test test_vault_missing_silent            test_vault_missing_silent
run_test test_post_compact_force_writes       test_post_compact_force_writes
run_test test_post_compact_empty_stdin        test_post_compact_empty_stdin

print_summary
