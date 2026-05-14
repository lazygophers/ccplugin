#!/usr/bin/env bash
# cortex/scripts/refresh_projects.sh — 静态源文件 (install_wrappers.sh PR3 复制到 ~/.cortex/scripts/).
#
# 批量增量刷新 知识库/项目/<host>/<org>/<repo>/:
#   git repo  → shallow clone → diff last_commit_sha → 仅刷动文件
#   website   → re-crawl sitemap → 每页 SHA256 对比 content_hash
#
# 风格对齐 CLI 类 wrapper (digest evolution dispatch / ingest_remote), 加 flock 防并发.
set -euo pipefail

if [ -t 2 ] && [ -z "${NO_COLOR:-}" ]; then
  _CX_R=$'\033[1;31m'; _CX_C=$'\033[1;36m'; _CX_0=$'\033[0m'
else
  _CX_R=""; _CX_C=""; _CX_0=""
fi
err()    { printf '%s✗%s %s\n' "$_CX_R" "$_CX_0" "$1" >&2; exit "${2:-4}"; }
banner() { printf '%s▸%s cortex %s  %s\n' "$_CX_C" "$_CX_0" "$*" "$(date '+%H:%M:%S')" >&2; }

print_usage() {
  cat <<USAGE
Usage: refresh_projects.sh [-h|--help] [--vault PATH] [--scope HOST[/ORG[/REPO]]] [--dry-run]

cortex 批量增量刷新 知识库/项目/ — 扫全部项目, 仅 ingest 变动文件:
  git repo  → shallow clone → diff sha
  website   → SHA256 对比 content_hash

Options:
  -h, --help              Show this help and exit
  --vault PATH            vault 根 (默认 resolve_vault)
  --scope HOST[/ORG[/REPO]]
                          限定 host / org / repo
  --dry-run               仅扫不更新, 输出 JSON

Examples:
  refresh_projects.sh
  refresh_projects.sh --scope github.com/foo/bar
  refresh_projects.sh --dry-run
USAGE
}

PASS_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) print_usage; exit 0 ;;
    *) PASS_ARGS+=("$1"); shift ;;
  esac
done

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
LOCK_FILE="/tmp/cortex-refresh.lock"

banner "refresh_projects"
printf '%s$%s flock -n %q python3 %q %s\n' \
  "$_CX_C" "$_CX_0" "$LOCK_FILE" \
  "$PLUGIN_ROOT/scripts/cli/refresh_projects.py" "${PASS_ARGS[*]:-}" >&2

if command -v flock >/dev/null 2>&1; then
  exec flock -n "$LOCK_FILE" python3 \
    "$PLUGIN_ROOT/scripts/cli/refresh_projects.py" "${PASS_ARGS[@]}"
fi
# flock 不可用 (macOS 默认无 flock) → 退回裸调
exec python3 "$PLUGIN_ROOT/scripts/cli/refresh_projects.py" "${PASS_ARGS[@]}"
