#!/usr/bin/env bash
# cortex/scripts/cron/memory-consolidate.sh — weekly ledger→views consolidation via claude --bare.
#
# Trigger: 30 04 * * 0   (weekly Sun 04:30)
# Frequency: weekly
# Duty: 上 7 天 L4 ledger + sessions 提炼周报 → views/consolidated/<YYYY-Wnn>.md;
#       识别重复模式 → candidates.md 追加 L3 提议; 跨领域连接 → 知识库/反思/连接/。
#
# Usage:
#   memory-consolidate.sh [--dry-run] [--vault <path>] [--lang <code>] [--settings <path>]

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
  echo "[cortex/memory-consolidate] no vault: pass --vault or set vault in ~/.cortex/config.json" >&2
  exit 3
fi
TIMEOUT_FLAG=(--timeout 900)

PROMPT="[AUTO_MODE: non-interactive shell wrapper. 禁用 AskUserQuestion, 自动决策]

任务: ledger → views 周报巩固 (memory-consolidate)。

vault: $VAULT

具体行动:
1. 计算上 7 天窗口 [now-7d, now] 与 ISO 周号 (YYYY-Wnn)。
2. 读输入:
   - <vault>/记忆/L4-流水账/ledger/*.jsonl 窗口内
   - <vault>/记忆/L4-流水账/sessions/*/YYYY-MM/* 窗口内
3. 提炼:
   - 高频实体/主题 top 20 (按出现次数排序)
   - 出现 ≥3 次的模式 (候选 L3 episodic→semantic 提议)
   - 跨领域 connections (同一会话/同一日不同领域的实体共现)
4. 写产物:
   a. <vault>/记忆/views/consolidated/<YYYY-Wnn>.md (整文件覆盖):
      frontmatter: type: view, week: YYYY-Wnn, generated: <UTC ISO>, generator: memory-consolidate
      分节: ## 高频实体 / ## 高频主题 / ## 重复模式 / ## 跨领域连接
   b. <vault>/记忆/views/candidates.md 追加 ## L4→L3 (consolidate <YYYY-Wnn>) 一节, 列出 ≥3 次模式作为提议 (uri: L3://episodic/<date>/...).
   c. <vault>/知识库/反思/连接/<YYYY-Wnn>.md (若有 ≥1 跨领域连接, 新建; 否则跳过):
      frontmatter: type: reflection, kind: connection, week: YYYY-Wnn
5. 不修改 ledger / sessions 原文件 (append-only 不变)。

输出: 一行 JSON { week: 'YYYY-Wnn', entities: N, patterns: N, connections: N, files_written: [...] }。
vault 不存在或窗口内无数据 → { skipped: true, reason: '<原因>' }。

工具预算: Bash Read Glob Write Edit。"

exec "$DIR/run.sh" memory-consolidate \
  ${VAULT_FLAG[@]+"${VAULT_FLAG[@]}"} ${LANG_FLAG[@]+"${LANG_FLAG[@]}"} ${SETTINGS_FLAG[@]+"${SETTINGS_FLAG[@]}"} ${TIMEOUT_FLAG[@]+"${TIMEOUT_FLAG[@]}"} ${DRY_FLAG[@]+"${DRY_FLAG[@]}"} \
  -- "$PROMPT" \
  --allowed-tools "Bash Read Glob Write Edit"
