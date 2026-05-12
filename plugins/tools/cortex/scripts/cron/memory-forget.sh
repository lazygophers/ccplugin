#!/usr/bin/env bash
# cortex/scripts/cron/memory-forget.sh — daily memory expiry marker via claude --bare.
#
# Trigger: 0 03 * * *   (daily 03:00)
# Frequency: daily
# Duty: 扫 L3/L2 过期条目, 在 frontmatter 标 archive_pending: true。
#       不删不移, 仅标记。memory-archive cron 才执行实际归档。
#
# Usage:
#   memory-forget.sh [--dry-run] [--vault <path>] [--lang <code>] [--settings <path>]

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
  echo "[cortex/memory-forget] no vault: pass --vault or set vault in ~/.cortex/config.json" >&2
  exit 3
fi
TIMEOUT_FLAG=(--timeout 600)

PROMPT="[AUTO_MODE: non-interactive shell wrapper. 禁用 AskUserQuestion, 自动决策]

任务: 标记过期记忆 (memory-forget)。

vault: $VAULT
policy: <vault>/_meta/memory-policy.yaml

具体行动:
1. 读 <vault>/_meta/memory-policy.yaml 的 levels.<L>.forget。默认:
   - L0: forget.never → 跳过
   - L1: forget.only_user → 跳过
   - L2: after_days=365, unless_recalled=5
   - L3: after_days=90, unless_recalled=3
   - L4: 由 memory-compact 处理 → 跳过
2. 扫描 <vault>/记忆/L3-短期/episodic/* 与 <vault>/记忆/L2-中期/semantic/* 的 .md 条目。
3. 读每个条目 frontmatter:
   - last_recalled (ISO 时间, 缺失则用 created)
   - recall_count (缺失视为 0)
   - archive_pending (已为 true → 跳过)
4. 判断过期:
   - L3: now - last_recalled > 90 天 且 recall_count < 3
   - L2: now - last_recalled > 365 天 且 recall_count < 5
5. 仅修改 frontmatter, 追加 archive_pending: true (用 Edit 工具, 保留原 frontmatter 其他字段不变)。不删文件, 不移文件。
6. 写日志到 <vault>/记忆/views/alerts.md (append 一节 ## memory-forget <UTC ISO>), 列出本次标记的 uri 清单。

输出: 一行 JSON 摘要 { L3_marked: N, L2_marked: N, skipped_already: N }。
vault 不存在 → { skipped: true, reason: 'no vault' }。

工具预算: Bash Read Glob Write Edit。"

exec "$DIR/run.sh" memory-forget \
  ${VAULT_FLAG[@]+"${VAULT_FLAG[@]}"} ${LANG_FLAG[@]+"${LANG_FLAG[@]}"} ${SETTINGS_FLAG[@]+"${SETTINGS_FLAG[@]}"} ${TIMEOUT_FLAG[@]+"${TIMEOUT_FLAG[@]}"} ${DRY_FLAG[@]+"${DRY_FLAG[@]}"} \
  -- "$PROMPT" \
  --allowed-tools "Bash Read Glob Write Edit"
