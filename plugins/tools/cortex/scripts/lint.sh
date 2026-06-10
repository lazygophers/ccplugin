#!/usr/bin/env bash
# lint.sh — cortex vault 合规检查与可逆 autofix
# 用法: lint.sh [--check|--fix] [--rules R1,R2,...] [--target <dir>] [--help]
# 默认 dry-run (--check); --fix 才落盘
set -euo pipefail

MODE="check"
RULES=""
TARGET="${HOME}/.cortex"

usage() {
  cat <<'EOF'
lint.sh — cortex vault 合规检查与 autofix

用法:
  lint.sh [--check|--fix] [--rules R1,R2,...] [--target <dir>]

参数:
  --check          仅检查 (默认), 报告违规并按 error 数退出
  --fix            落盘 autofix (仅 R2 frontmatter / R4 同构目录)
  --rules R1,R2    限定规则 (默认全部 R1-R7)
  --target <dir>   待检 vault 根 (默认 $HOME/.cortex)
  --help           显示本文档

规则:
  R1 wikilink (warn)    R2 frontmatter (error,fix)
  R3 命名 (warn)         R4 同构目录 (error,fix)
  R5 孤儿 (warn)         R6 等级语义 (error)
  R7 脚本目录 (warn)

退出:
  0  无 error
  1  有 error (--check) 或 fix 失败 (--fix)
  2  参数错误
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) MODE="check"; shift ;;
    --fix)   MODE="fix"; shift ;;
    --rules) RULES="$2"; shift 2 ;;
    --target) TARGET="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ ! -d "$TARGET" ]]; then
  echo "ERROR: target not a directory: $TARGET" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/_lint/runner.py" \
  --mode "$MODE" \
  --target "$TARGET" \
  ${RULES:+--rules "$RULES"}
