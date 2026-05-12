---
description: 跑晋级候选检测 — L4→L3 / L3→L2 auto, L2→L0 写候选 (无入参)
---

# /cortex:promote

[AUTO_MODE persistent: 禁询问, 自决执行, 禁中止]

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

## AUTO_MODE (shell wrapper 触发, persistent)

**核心原则**: "禁问" ≠ "中止". AI 必须**自决并执行直至任务完成**。遇歧义按推荐默认值执行; 工具不熟悉则尝试其他工具组合 (Bash/Edit/Write/MCP/WebSearch/WebFetch/Read 现有样本); 禁报"需人工"/"AI 不会"/"建议后续处理"。

### 严禁 (任一出现 = 契约违反)

| # | 禁止 |
|---|------|
| 1 | 任何"修复建议"/"建议"/"推荐操作" 章节/表格/列表 (`## 修复建议`, `\| 类型 \| 操作 \|`) |
| 2 | 用户确认问句 (`需确认?`, `是否执行?`, `要继续吗?`, `ok?`, 末尾问号) |
| 3 | AskUserQuestion 调用 (allowed-tools 已禁) |
| 4 | "下一步"/"后续"/"如需"/"可选" 导引 |
| 5 | "需人工"/"待人工"/"建议人工" 推卸辞令 |
| 6 | "AI 能力不足"/"无法自动" 类借口 |
| 7 | 报状态后停 (除非工具客观失败: 磁盘只读/权限拒绝/git lock) |
