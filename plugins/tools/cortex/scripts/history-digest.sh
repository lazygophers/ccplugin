#!/usr/bin/env bash
# history-digest.sh — 扫 ~/.claude/projects/**/*.jsonl 历史 transcripts
# 提取学习增量 → 路由到全局 ~/.cortex/.wiki/memory/ (L0-L4)
# 默认 apply; --dry-run opt-in 预览 JSON plan. --apply 标 "需 main 后处理" (本 task 范围不实写).
set -euo pipefail

MODE="apply"
TARGET="${HOME}/.cortex"
SOURCE_ROOT="${HOME}/.claude/projects"
SINCE=""

usage() {
  cat <<'EOF'
history-digest.sh — Claude Code 会话历史 → 全局记忆库

用法:
  history-digest.sh [--dry-run|--apply] [--target <vault>] [--source-root <dir>] [--since <YYYY-MM-DD>] [--help]

参数:
  --dry-run         仅输出 JSON plan (opt-in 预览)
  --apply           默认. 标 "需 main 后处理" — 本 task 范围不实写
  --target <d>      vault 根 (默认 $HOME/.cortex), 写入 .wiki/memory/L*
  --source-root <d> Claude Code projects 根 (默认 $HOME/.claude/projects)
  --since <date>    仅处理该日期以后的 session (YYYY-MM-DD, 后续可加游标)
  --help            显示本文档

学习增量识别 (extractor.py):
  user-correction  用户校正 (no/wrong/不对/别这样)        → L1/L2 候选
  L0-rule          L0 关键词 (永远/硬性/never/严禁/绝不) → L0-core (自动)
  decision         决策语 (let's use/我们选/决定)         → L2/L3 候选
  tip              踩坑 (failed/error because/踩坑/坑)    → L2 候选

路由 (router.py, 全部全局):
  按 cortex-schema/references/memory-levels.md 5 级映射.

退出:
  0  成功
  1  source-root 不存在 / 解析全失败
  2  参数错误
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)    MODE="dry-run"; shift ;;
    --apply)      MODE="apply"; shift ;;
    --target)     TARGET="$2"; shift 2 ;;
    --source-root) SOURCE_ROOT="$2"; shift 2 ;;
    --since)      SINCE="$2"; shift 2 ;;
    --help|-h)    usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ ! -d "$SOURCE_ROOT" ]]; then
  echo "ERROR: source-root not a directory: $SOURCE_ROOT" >&2
  exit 1
fi
SOURCE_ROOT="$(cd "$SOURCE_ROOT" && pwd)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
ARGS=(--mode "$MODE" --target "$TARGET" --source-root "$SOURCE_ROOT")
[[ -n "$SINCE" ]] && ARGS+=(--since "$SINCE")
exec python3 -m _history_digest.runner "${ARGS[@]}"
