#!/usr/bin/env bash
# ingest.sh — 知识库构建: GitHub/GitLab/Website URL 或 local dir → 项目/<host>/<owner>/<repo>/
# 默认 dry-run JSON plan; --apply 当前 task 范围仍为 plan + "需 main 抓取" 提示.
set -euo pipefail

MODE="dry-run"
TARGET="${HOME}/.cortex"
SOURCE=""

usage() {
  cat <<'EOF'
ingest.sh — cortex 知识库构建 (项目/ 模块)

用法:
  ingest.sh [--dry-run|--apply] [--target <vault-root>] --source <url-or-path> [--help]

参数:
  --dry-run     仅输出 JSON plan (默认)
  --apply       本 task 范围: 输出 plan + "需 main 抓取" 标记 (不直接落盘)
  --target <d>  vault 根 (默认 $HOME/.cortex)
  --source <s>  必填. URL (https://github.com/.. / https://gitlab.com/.. / https://<domain>/..)
                或 ssh git URL (git@github.com:owner/repo.git) 或 local dir 路径
  --help        显示本文档

输入识别 (优先序):
  1. URL pattern: github.com / gitlab.com / 其他 → website
  2. ssh git URL: git@<host>:<owner>/<repo>(.git)? → github/gitlab
  3. local dir + .git/config remote → 按 remote URL 递归识别
  4. local dir 无 git → 项目/local/<basename>/

目标路径:
  github/gitlab → 项目/<host>/<owner>/<repo>/
  website       → 项目/<domain>/_/<path-slug>/
  local         → 项目/local/<dir-basename>/

退出:
  0  plan 生成 OK
  2  参数错误
  1  路由 / 识别失败
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) MODE="dry-run"; shift ;;
    --apply)   MODE="apply"; shift ;;
    --target)  TARGET="$2"; shift 2 ;;
    --source)  SOURCE="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$SOURCE" ]]; then
  echo "ERROR: --source required" >&2
  usage >&2
  exit 2
fi

# Resolve SOURCE 到绝对路径 (仅当看起来是本地路径时), 防 cd SCRIPT_DIR 后失效
if [[ "$SOURCE" != http://* && "$SOURCE" != https://* && "$SOURCE" != git@* && -e "$SOURCE" ]]; then
  SOURCE="$(cd "$(dirname "$SOURCE")" && pwd)/$(basename "$SOURCE")"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
exec python3 -m _ingest.runner \
  --mode "$MODE" \
  --target "$TARGET" \
  --source "$SOURCE"
