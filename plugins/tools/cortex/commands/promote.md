---
description: 跑晋级候选检测 — L4→L3 / L3→L2 auto, L2→L0 写候选 (无入参)
---

# /cortex:promote

[AUTO_MODE strict: 禁询问, fail-fast]

按 `_meta/memory-policy.yaml` + cortex-promote SKILL 流程检测晋级候选:

1. 从 `~/.cortex/config.json` 读 vault
2. 扫 L4 ledger 上 7 天: freq ≥ 3 → L3 候选; freq ≥ 5 跨 ≥3 天 → L2 候选; freq ≥ 10 跨 ≥30 天 → L1 候选
3. 扫 L3 episodic 上 30 天: 同主题 ≥ 5 + last_recalled 增长 → L2 候选
4. 扫 L2 semantic 上 365 天: recall_count ≥ 20 且 90 天 weight 稳定 → L1 候选
5. L0 永不自动 (仅写 candidates 供用户审批)

执行规则:
- L4→L3 / L3→L2: auto promote
- L2→L1 / L1→L0: 仅写 `views/candidates.md`

输出: `views/candidates.md` 表格 (候选 / 来源 level / 目标 level / freq / timespan / weight / 理由)。
