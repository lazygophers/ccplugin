#!/usr/bin/env bash
# extract.sh — L4-inbox → L1/L2/L3 + projects/domains 路由提取
# 默认 apply 落盘; --dry-run opt-in 预览. 增量游标: <target>/state/extract-cursor.json
set -euo pipefail

MODE="apply"
TARGET="${HOME}/.cortex"
NO_CURSOR=0

usage() {
  cat <<'EOF'
extract.sh — cortex L4-inbox 提取与路由

用法:
  extract.sh [--dry-run|--apply] [--target <dir>] [--no-cursor] [--help]

参数:
  --dry-run     仅输出 JSON plan (opt-in 预览)
  --apply       落盘到目标 + 更新游标 + archive 原 inbox 条目 (默认)
  --target <d>  vault 根 (默认 $HOME/.cortex), 内部期望含 .wiki/memory/L4-inbox/
  --no-cursor   忽略游标, 全量扫
  --help        显示本文档

路由 (按 cortex-schema):
  关键词 L0 (永远/硬性/never/严禁) → L0-core (自动落盘)
  URL (github/gitlab/https://)     → projects/<host>/<owner>/<repo>/
  frontmatter area + type=domain   → domains/<area>/<sub|general>/
  L1 关键词 (永久记住)              → L1-long
  L2 关键词 (记住/以后也用)         → L2-mid
  默认 / L3 关键词 (暂时/临时)      → L3-short
  复用 ≥ 3 → 附加 promote-L2 标记 (仍落 L3)
  复用 ≥ 5 + weight ≥ 0.8 → 附加 promote-L1 标记

L0 写入默认自动落盘 (不再 ask). 可用环境变量 CORTEX_EXTRACT_L0_AUTO ∈ {accept, reject}
覆盖 (默认 accept; 设 reject 可跳过 L0 项)

退出:
  0  成功
  1  路由 / 落盘错误
  2  参数错误
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) MODE="dry-run"; shift ;;
    --apply)   MODE="apply"; shift ;;
    --target)  TARGET="$2"; shift 2 ;;
    --no-cursor) NO_CURSOR=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *)
      # 兼容位置参数: 把首个非选项当 target
      if [[ -z "${TARGET_SET:-}" && ! "$1" =~ ^-- ]]; then
        TARGET="$1"; TARGET_SET=1; shift
      else
        echo "unknown arg: $1" >&2; usage >&2; exit 2
      fi
      ;;
  esac
done

if [[ ! -d "$TARGET" ]]; then
  echo "ERROR: target not a directory: $TARGET" >&2
  exit 2
fi
TARGET="$(cd "$TARGET" && pwd)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
exec python3 -m _extract.runner \
  --mode "$MODE" \
  --target "$TARGET" \
  $([[ $NO_CURSOR -eq 1 ]] && echo "--no-cursor")
