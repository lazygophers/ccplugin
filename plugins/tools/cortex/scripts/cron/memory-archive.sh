#!/usr/bin/env bash
# cortex/scripts/cron/memory-archive.sh — monthly archive execution via claude --bare.
#
# Trigger: 0 06 1 * *   (1st of month, 06:00)
# Frequency: monthly
# Duty: 扫 archive_pending: true 的记忆条目 → mv 到 归档/<year>/记忆/<level>/<原路径>;
#       更新 _meta/uri-index.json (标 archived: true)。L0 永不归档。
#
# Usage:
#   memory-archive.sh [--dry-run] [--vault <path>] [--lang <code>] [--settings <path>]

set -uo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/config.sh
source "$DIR/../lib/config.sh"
cortex_config_init

DRY_FLAG=()
VAULT_FLAG=()
LANG_FLAG=()
SETTINGS_FLAG=()
CLI_VAULT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)  DRY_FLAG=(--dry-run);              shift ;;
    --vault)    CLI_VAULT="$2"; VAULT_FLAG=(--vault "$2"); shift 2 ;;
    --lang)     LANG_FLAG=(--lang "$2");           shift 2 ;;
    --settings) SETTINGS_FLAG=(--settings "$2");   shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 4 ;;
  esac
done


VAULT="${CLI_VAULT:-$(cx_get_vault)}"
if [[ -z "$VAULT" ]]; then
  echo "[cortex/memory-archive] no vault: pass --vault or set vault in ~/.cortex/config.json" >&2
  exit 3
fi
TIMEOUT_FLAG=(--timeout 900)

PROMPT="[AUTO_MODE: non-interactive shell wrapper. 禁用 AskUserQuestion, 自动决策]

任务: 归档已标记记忆 (memory-archive)。

vault: $VAULT

具体行动:
1. 扫 <vault>/记忆/**/*.md, 读 frontmatter 找 archive_pending: true 的条目。
2. 对每个候选:
   - 若 level == L0 → 跳过 + 写报警到 <vault>/记忆/views/alerts.md (L0 永不归档, 即使被错误标记)
   - 其他 level: 计算目标路径:
       src: <vault>/记忆/<level-dir>/<rest>
       dst: <vault>/归档/\$(date +%Y)/记忆/<level-dir>/<rest>
     用 Bash mkdir -p <dst 父目录> + mv <src> <dst>。
3. 更新 <vault>/_meta/uri-index.json (若存在):
   - 对应 uri 节点添加字段 archived: true, archived_at: <UTC ISO>, archived_path: <相对路径>
   - 不删除条目 (仍可通过 uri 解析到归档位置)
4. 不删条目内容, 只迁移路径 + 标 index。
5. 写日志到 <vault>/_meta/memory-archive.log (append 一行 \`<UTC ISO>: archived=N, skipped_l0=N\`)。

输出: 一行 JSON { archived: N, skipped_l0: N, index_updated: true|false }。
vault 不存在 → { skipped: true, reason: 'no vault' }。

工具预算: Bash Read Glob Write Edit。"

exec "$DIR/run.sh" memory-archive \
  ${VAULT_FLAG[@]+"${VAULT_FLAG[@]}"} ${LANG_FLAG[@]+"${LANG_FLAG[@]}"} ${SETTINGS_FLAG[@]+"${SETTINGS_FLAG[@]}"} ${TIMEOUT_FLAG[@]+"${TIMEOUT_FLAG[@]}"} ${DRY_FLAG[@]+"${DRY_FLAG[@]}"} \
  -- "$PROMPT" \
  --allowed-tools "Bash Read Glob Write Edit"
