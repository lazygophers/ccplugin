#!/usr/bin/env bash
# cortex tests entry point.
# Runs all python + bash tests in sequence; exits 0 only if all pass.
#
# Usage:
#   bash plugins/tools/cortex/tests/run.sh           # run everything
#   bash plugins/tools/cortex/tests/run.sh python    # python only
#   bash plugins/tools/cortex/tests/run.sh bash      # bash only
#   bash plugins/tools/cortex/tests/run.sh --coverage  # python + bash + coverage report

set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/.." && pwd)"

MODE="all"
COVERAGE=0
for arg in "$@"; do
  case "$arg" in
    python|bash|all) MODE="$arg" ;;
    --coverage) COVERAGE=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

red()   { printf '\033[31m%s\033[0m' "$*"; }
green() { printf '\033[32m%s\033[0m' "$*"; }
bold()  { printf '\033[1m%s\033[0m' "$*"; }

PY_FAIL=0
BASH_FAIL=0
PY_TESTS_RUN=0
BASH_TESTS_RUN=0

if [[ "$MODE" == "all" || "$MODE" == "python" ]]; then
  printf '\n%s\n' "$(bold '== Python tests ==')"
  cd "$DIR/python"
  if [[ "$COVERAGE" == "1" ]] && command -v coverage >/dev/null 2>&1; then
    coverage run -m unittest discover -s . -p 'test_*.py' -v 2>&1 | tee /tmp/cortex-py-results.txt || PY_FAIL=1
  else
    python3 -m unittest discover -s . -p 'test_*.py' -v 2>&1 | tee /tmp/cortex-py-results.txt
    PY_FAIL=${PIPESTATUS[0]}
  fi
  PY_TESTS_RUN=$(grep -Eo 'Ran [0-9]+ tests' /tmp/cortex-py-results.txt | tail -1 | grep -Eo '[0-9]+' || echo 0)
fi

if [[ "$MODE" == "all" || "$MODE" == "bash" ]]; then
  printf '\n%s\n' "$(bold '== Bash tests ==')"
  for f in "$DIR/bash"/test_*.sh; do
    printf '\n--- %s ---\n' "$(basename "$f")"
    bash "$f" || BASH_FAIL=1
    BASH_TESTS_RUN=$((BASH_TESTS_RUN + 1))
  done
fi

if [[ "$COVERAGE" == "1" ]] && command -v coverage >/dev/null 2>&1; then
  printf '\n%s\n' "$(bold '== Coverage ==')"
  cd "$DIR/python"
  coverage report --include="$PLUGIN_ROOT/hooks/_lib/*,$PLUGIN_ROOT/lint/*,$PLUGIN_ROOT/refactor/*" 2>/dev/null || true
fi

printf '\n%s\n' "$(bold '== Summary ==')"
printf '  python: %s (%s tests)\n' "$([[ $PY_FAIL -eq 0 ]] && green PASS || red FAIL)" "$PY_TESTS_RUN"
printf '  bash:   %s (%s files)\n'  "$([[ $BASH_FAIL -eq 0 ]] && green PASS || red FAIL)" "$BASH_TESTS_RUN"

if [[ $PY_FAIL -ne 0 || $BASH_FAIL -ne 0 ]]; then
  exit 1
fi
exit 0
