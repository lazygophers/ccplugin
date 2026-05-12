#!/usr/bin/env bash
# cortex/scripts/cron/memory-warden.sh — biweekly memory corruption audit via claude --bare.
#
# Trigger: 0 05 1,15 * *   (1st & 15th of month, 05:00)
# Frequency: biweekly
# Duty: 腐化检测 (L0 完整性 / L1-L2 矛盾 / 时效失效 / 反馈自增强), 写监控看板 + alerts。
#
# Usage:
#   memory-warden.sh [--dry-run] [--vault <path>] [--lang <code>] [--settings <path>]

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
  echo "[cortex/memory-warden] no vault: pass --vault or set vault in ~/.cortex/config.json" >&2
  exit 3
fi
TIMEOUT_FLAG=(--timeout 900)

PROMPT="[AUTO_MODE: non-interactive shell wrapper. 禁用 AskUserQuestion, 自动决策]

任务: 记忆腐化检测 (memory-warden)。

vault: $VAULT

具体行动:
1. L0 完整性: 若 <vault>/.git 存在, 跑 \`git -C <vault> log --format=%H -- 记忆/L0-核心/\` + \`git -C <vault> tag --contains <commit>\` 检查 L0 改动是否有 git tag 锚定。无 tag 的 L0 改动 → 严重报警。
2. L1/L2 矛盾: 扫 <vault>/记忆/L1-长期/{procedural,semantic-stable}/* 与 L2-中期/semantic/* 的 frontmatter (尤其 ref/topic 字段) 与 brief。同 topic 多条目语义冲突 (AI 判读, 谨慎假阳) → 中度报警。
3. 时效失效: 扫所有记忆条目 frontmatter expires, 若 expires < now 且无 archive_pending → 列出。
4. 反馈自增强: 扫 git 历史 (若有) 或 frontmatter weight 字段连续 ≥4 次单调上升 且 last_recalled 期间未变 → 标可疑。
5. 写产物:
   a. <vault>/仪表盘/记忆-腐化监控.md (整文件覆盖):
      frontmatter: type: dashboard, generated: <UTC ISO>, generator: memory-warden
      分节: ## L0 完整性 / ## L1-L2 矛盾 / ## 时效失效 / ## 反馈自增强
      每节列发现项 (uri / 描述 / 严重度: high/medium/low)
   b. <vault>/记忆/views/alerts.md 追加 ## memory-warden <UTC ISO> 一节, 仅记 severity=high 项。
6. 不修改任何记忆条目本身 (只读 + 写看板/alerts)。

输出: 一行 JSON { l0_violations: N, contradictions: N, expired: N, suspicious_weight: N }。
vault 不存在 → { skipped: true, reason: 'no vault' }。

工具预算: Bash Read Glob Write Edit。"

exec "$DIR/run.sh" memory-warden \
  ${VAULT_FLAG[@]+"${VAULT_FLAG[@]}"} ${LANG_FLAG[@]+"${LANG_FLAG[@]}"} ${SETTINGS_FLAG[@]+"${SETTINGS_FLAG[@]}"} ${TIMEOUT_FLAG[@]+"${TIMEOUT_FLAG[@]}"} ${DRY_FLAG[@]+"${DRY_FLAG[@]}"} \
  -- "$PROMPT" \
  --allowed-tools "Bash Read Glob Write Edit"
