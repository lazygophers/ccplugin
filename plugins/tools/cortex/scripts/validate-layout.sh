#!/usr/bin/env bash
# validate-layout.sh — cortex 目录契约校验
# 用法: validate-layout.sh [--target <dir>] [--help]
# 退出: 0 = 全部必备项存在; 非 0 = 至少 1 项缺失
set -euo pipefail

TARGET="${HOME}/.cortex"

usage() {
  cat <<'EOF'
validate-layout.sh — cortex 目录契约校验

用法:
  validate-layout.sh [--target <dir>]

参数:
  --target <dir>   待校验根目录 (默认 $HOME/.cortex)
  --help           显示本文档

校验项 (必备):
  顶层:    .wiki/  config/  state/  scripts/  logs/
           ↑ scripts/ = 用户操作入口 CLI
  .wiki/:  memory/L0-core  memory/L1-long  memory/L2-mid
           memory/L3-short  memory/L4-inbox
           项目/  领域/  脚本/
           ↑ 脚本/ = vault 内部脚本 (与顶层 scripts/ 用户操作入口分离)

非必备 (允许存在, 不强制):
  顶层:    cache/  credentials/  templates/  及任何用户扩展位

退出:
  0  全部必备项存在
  1  至少 1 项缺失 (详情到 stderr)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ ! -d "$TARGET" ]]; then
  echo "ERROR: target not a directory: $TARGET" >&2
  exit 1
fi

REQUIRED=(
  ".wiki"
  ".wiki/memory"
  ".wiki/memory/L0-core"
  ".wiki/memory/L1-long"
  ".wiki/memory/L2-mid"
  ".wiki/memory/L3-short"
  ".wiki/memory/L4-inbox"
  ".wiki/项目"
  ".wiki/领域"
  ".wiki/脚本"
  "config"
  "state"
  "scripts"
  "logs"
)

MISSING=()
for path in "${REQUIRED[@]}"; do
  if [[ ! -d "$TARGET/$path" ]]; then
    MISSING+=("$path")
  fi
done

# 防呆: 检测反直觉路径名 (L1-recent / L1-short / L3-long 等)
BAD_NAMES=()
for bad in "L1-recent" "L1-short" "L2-short" "L2-long" "L3-long" "L3-recent" "L0-rules"; do
  if [[ -d "$TARGET/.wiki/memory/$bad" ]]; then
    BAD_NAMES+=("$bad")
  fi
done

if [[ ${#MISSING[@]} -gt 0 ]] || [[ ${#BAD_NAMES[@]} -gt 0 ]]; then
  for p in "${MISSING[@]}"; do
    echo "MISSING: $TARGET/$p" >&2
  done
  for b in "${BAD_NAMES[@]}"; do
    echo "BAD-NAME (反直觉等级路径): $TARGET/.wiki/memory/$b" >&2
  done
  echo "FAIL: missing=${#MISSING[@]} bad-name=${#BAD_NAMES[@]}" >&2
  exit 1
fi

echo "OK: ${#REQUIRED[@]} required paths present at $TARGET"
exit 0
