#!/usr/bin/env bash
# cortex/scripts/cron/digest.sh — daily log/session 五阶段处理.
#
# 读 (Read) + 析 (Analyze) + 处 (Process) + 更新 (Update) + 清理 + 归档 (Cleanup + Archive).
#
# Trigger: 0 3 * * *  (每日 03:00)
# Frequency: daily
# Duty:
#   - 读 L4 ledger / L4 sessions / 知识库/日记 近 24h
#   - 析: 模式聚合 / 实体频度 / 决策提炼 / 疑问识别
#   - 处: 写 views/consolidated/<YYYY-MM-DD>.md + reflection + candidates
#   - 更新: uri-index 重建 + L4→L3 frequency-based 自动升
#   - 清理: 删 L4 ledger > 30d 未升 / L3 > 90d weight<0.3 / 反思已概念化页
#
# Usage:
#   digest.sh [--dry-run] [--vault <path>] [--lang <code>] [--settings <path>]

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
CLI_LANG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)  DRY_FLAG=(--dry-run);             shift ;;
    --vault)    CLI_VAULT="$2"; VAULT_FLAG=(--vault "$2"); shift 2 ;;
    --lang)     CLI_LANG="$2"; LANG_FLAG=(--lang "$2");    shift 2 ;;
    --settings) SETTINGS_FLAG=(--settings "$2");           shift 2 ;;
    *) echo "[cortex/consolidate] unknown flag: $1" >&2; exit 4 ;;
  esac
done

VAULT="${CLI_VAULT:-$(cx_get_vault)}"
if [[ -z "$VAULT" ]]; then
  echo "[cortex/consolidate] no vault: pass --vault or set 'vault' in ~/.cortex/config.json" >&2
  exit 3
fi
LANG_CODE="${CLI_LANG:-$(cx_config_get lang "")}"

PROMPT="Run cortex-digest daily five-phase pipeline on vault at $VAULT (lang ${LANG_CODE:-zh-CN}).
Phases:
1) Read FULL L4-流水账 recursively — ALL files of ANY type (md/jsonl/json/yaml/js/ts/sh/py/txt/log) under 记忆/L4-流水账/**. NO time window, NO type filter. Every L4 file must be processed in phase 5.
   Also read 知识库/收件箱/*.md (all) + 知识库/日记/日/<YYYY-MM>/ (all).
2) Analyze patterns/entities/decisions/questions. jsonl → per-line parse; json/yaml → structured parse; other → paragraph scan.
3) Process to views/consolidated/<YYYY-MM-DD>.md + reflection + candidates.
4) Update uri-index + L4→L3 promote (frequency >= 5).
5) Cleanup — L4-流水账 MUST be FULLY drained (NO time window, NO exemption): EVERY file (any type, any age) exits L4 via promote-L3 | archive-to-归档/L4-<YYYY>/<rel> | delete. After digest, 记忆/L4-流水账/** MUST be empty (0 files). L4 is single-pass funnel, never accumulates.
   ALSO drain L3 (>90d weight<0.3), concretized questions (backlinks >= 3), inbox (>=30d MUST classify|archive|delete; <30d untouched), 知识库/日记/日 (>7d → 归档/日记/<YYYY-QN>.md quarterly bucket, idempotent).
   do NOT touch 记忆/L0-核心 or 记忆/L1-长期.
Output compact JSON: {date, read:{ledger,sessions,logs,inbox,l4_other}, analyzed, written, updated, cleaned:{l4_promoted,l4_archived,l4_deleted,L3_purged,questions_purged,inbox_classified,inbox_archived,inbox_deleted}}."

exec "$DIR/run.sh" consolidate \
  ${VAULT_FLAG[@]+"${VAULT_FLAG[@]}"} \
  ${LANG_FLAG[@]+"${LANG_FLAG[@]}"} \
  ${SETTINGS_FLAG[@]+"${SETTINGS_FLAG[@]}"} \
  ${DRY_FLAG[@]+"${DRY_FLAG[@]}"} \
  -- "$PROMPT"
