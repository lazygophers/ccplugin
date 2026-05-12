#!/usr/bin/env bash
# cortex/scripts/cron/memory-promote.sh — daily memory-promote candidate scan via claude --bare.
#
# Trigger: 0 02 * * *   (daily 02:00)
# Frequency: daily
# Duty: 扫描 L4→L3 / L3→L2 / L2→L1 晋级候选, 写候选清单到 views/candidates.md。
#       不自动晋级; L1→L0 必须用户审批。
#
# Usage:
#   memory-promote.sh [--dry-run] [--vault <path>] [--lang <code>] [--settings <path>]

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
  echo "[cortex/memory-promote] no vault: pass --vault or set vault in ~/.cortex/config.json" >&2
  exit 3
fi
TIMEOUT_FLAG=(--timeout 600)

PROMPT="[AUTO_MODE: non-interactive shell wrapper. 禁用 AskUserQuestion, 自动决策]

任务: 扫描记忆晋级候选 (memory-promote)。

vault: $VAULT
policy: <vault>/_meta/memory-policy.yaml

具体行动:
1. 读 <vault>/_meta/memory-policy.yaml 取各 level 的 promote_criteria。若 policy 缺失, 用以下三层重复检测默认算法:

   扫 L4 ledger 上 7 天:
     - 统计 (entity, topic, context) 三元组频率
     - freq ≥ 3 → 创建 L3 episodic 候选, auto promote (L4→L3)
     - freq ≥ 5 + 跨 ≥3 天 → L3 → L2 候选 (写 candidates.md, 不自动)
     - freq ≥ 10 + 跨 ≥30 天 → L2 → L1 候选

   扫 L3 episodic 上 30 天:
     - 同 topic ≥ 5 次 + last_recalled 增长 → L2 候选

   扫 L2 semantic 上 365 天:
     - recall_count ≥ 20 + stable (90 天无 weight 大改) → L1 候选

   L0 永不自动 (用户审批必经); L1→L0 仅写候选, needs_user_approval: true。

2. 扫描:
   - <vault>/记忆/L4-流水账/ledger/*.jsonl (近 7 天)
   - <vault>/记忆/L3-短期/episodic/* (近 30 天)
   - <vault>/记忆/L2-中期/semantic/* (近 365 天)
   - <vault>/记忆/L1-长期/{procedural,semantic-stable}/*
3. 读各条目 frontmatter (uri/level/weight/recall_count/last_recalled/created), 评估晋级条件。
4. 写候选清单到 <vault>/记忆/views/candidates.md (整文件覆盖, 不 append):
   - 顶部 frontmatter: type: view, generated: <UTC ISO>, generator: memory-promote
   - 分节: ## L4→L3 / ## L3→L2 / ## L2→L1 / ## L1→L0 (needs_user_approval)
   - 表格列: | 候选 URI | 源 level | 目标 level | freq | timespan | weight | 建议理由 |
5. 不修改原条目 (不写 promote_eligible: true 到 frontmatter, 仅候选清单)。L1→L0 候选额外标 needs_user_approval: true。L4→L3 可执行 auto promote (写新 L3 条目); 其余仅候选。

输出: 一行 JSON 摘要 { L4_to_L3: N, L3_to_L2: N, L2_to_L1: N, L1_to_L0: N, candidates_file: 'views/candidates.md' }。
若 vault 不存在或 _meta/memory-policy.yaml 缺失 → 输出 { skipped: true, reason: '<原因>' } 并正常退出。

工具预算: Bash Read Glob Write Edit。"

exec "$DIR/run.sh" memory-promote \
  ${VAULT_FLAG[@]+"${VAULT_FLAG[@]}"} ${LANG_FLAG[@]+"${LANG_FLAG[@]}"} ${SETTINGS_FLAG[@]+"${SETTINGS_FLAG[@]}"} ${TIMEOUT_FLAG[@]+"${TIMEOUT_FLAG[@]}"} ${DRY_FLAG[@]+"${DRY_FLAG[@]}"} \
  -- "$PROMPT" \
  --allowed-tools "Bash Read Glob Write Edit"
