#!/usr/bin/env bash
# Tiny assert library for bash tests.
# Source from each test_*.sh. On failure, exits 1 and prints location.

set -u

_TESTS_RUN=0
_TESTS_FAIL=0
_CUR_TEST=""

_red()   { printf '\033[31m%s\033[0m' "$*"; }
_green() { printf '\033[32m%s\033[0m' "$*"; }
_yellow(){ printf '\033[33m%s\033[0m' "$*"; }

assert_eq() {
  local expected="$1" actual="$2" msg="${3:-}"
  _TESTS_RUN=$((_TESTS_RUN + 1))
  if [[ "$expected" == "$actual" ]]; then
    return 0
  fi
  _TESTS_FAIL=$((_TESTS_FAIL + 1))
  printf '  %s in %s\n' "$(_red FAIL)" "$_CUR_TEST"
  printf '    expected: %s\n' "$expected"
  printf '    actual:   %s\n' "$actual"
  [[ -n "$msg" ]] && printf '    msg: %s\n' "$msg"
}

assert_neq() {
  local expected="$1" actual="$2" msg="${3:-}"
  _TESTS_RUN=$((_TESTS_RUN + 1))
  if [[ "$expected" != "$actual" ]]; then
    return 0
  fi
  _TESTS_FAIL=$((_TESTS_FAIL + 1))
  printf '  %s in %s: values equal (%s)\n' "$(_red FAIL)" "$_CUR_TEST" "$expected"
  [[ -n "$msg" ]] && printf '    msg: %s\n' "$msg"
}

assert_contains() {
  local needle="$1" haystack="$2" msg="${3:-}"
  _TESTS_RUN=$((_TESTS_RUN + 1))
  if [[ "$haystack" == *"$needle"* ]]; then
    return 0
  fi
  _TESTS_FAIL=$((_TESTS_FAIL + 1))
  printf '  %s in %s\n' "$(_red FAIL)" "$_CUR_TEST"
  printf '    expected to contain: %s\n' "$needle"
  printf '    actual: %s\n' "${haystack:0:200}"
  [[ -n "$msg" ]] && printf '    msg: %s\n' "$msg"
}

assert_not_contains() {
  local needle="$1" haystack="$2" msg="${3:-}"
  _TESTS_RUN=$((_TESTS_RUN + 1))
  if [[ "$haystack" != *"$needle"* ]]; then
    return 0
  fi
  _TESTS_FAIL=$((_TESTS_FAIL + 1))
  printf '  %s in %s\n' "$(_red FAIL)" "$_CUR_TEST"
  printf '    expected NOT to contain: %s\n' "$needle"
  printf '    actual: %s\n' "${haystack:0:200}"
  [[ -n "$msg" ]] && printf '    msg: %s\n' "$msg"
}

assert_empty() {
  local actual="$1" msg="${2:-}"
  _TESTS_RUN=$((_TESTS_RUN + 1))
  if [[ -z "$actual" ]]; then
    return 0
  fi
  _TESTS_FAIL=$((_TESTS_FAIL + 1))
  printf '  %s in %s: expected empty, got: %s\n' \
    "$(_red FAIL)" "$_CUR_TEST" "${actual:0:120}"
  [[ -n "$msg" ]] && printf '    msg: %s\n' "$msg"
}

assert_file_exists() {
  local path="$1"
  _TESTS_RUN=$((_TESTS_RUN + 1))
  if [[ -e "$path" ]]; then
    return 0
  fi
  _TESTS_FAIL=$((_TESTS_FAIL + 1))
  printf '  %s in %s: file not found: %s\n' "$(_red FAIL)" "$_CUR_TEST" "$path"
}

run_test() {
  local name="$1"; shift
  _CUR_TEST="$name"
  local before_fail=$_TESTS_FAIL
  "$@"
  if [[ $_TESTS_FAIL -gt $before_fail ]]; then
    printf '%s %s\n' "$(_red ✗)" "$name"
  else
    printf '%s %s\n' "$(_green ✓)" "$name"
  fi
}

print_summary() {
  if [[ $_TESTS_FAIL -eq 0 ]]; then
    printf '\n%s: %d assertions passed\n' "$(_green PASS)" "$_TESTS_RUN"
    return 0
  fi
  printf '\n%s: %d/%d assertions failed\n' "$(_red FAIL)" "$_TESTS_FAIL" "$_TESTS_RUN"
  return 1
}

# Make a sandboxed temp dir; auto-cleaned via trap
make_tmpdir() {
  local d
  d="$(mktemp -d -t cortex-test-XXXXXX)"
  printf '%s' "$d"
}
