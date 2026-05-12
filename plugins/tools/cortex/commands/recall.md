---
description: 渐进披露召回 query 相关记忆 — 无入参时列 top 10 hot
---

# /cortex:recall

[AUTO_MODE strict: 禁询问, fail-fast]

渐进披露召回。

1. 从 `~/.cortex/config.json` 读 vault
2. **若 wrapper 无入参调用 (默认)**: 列 `hot.md` top 10 (按 recall_count + last_recalled 排序) + 各 level brief 计数
3. 若有显式 args (query): 按 cortex-recall SKILL 流程多级回退 (hot → uri-index → semantic → rg)
   - 默认: `top_k=5`, `levels=L0,L1,L2,L3` (排除 L4 raw ledger)

输出: brief + 子节点列表 (URI / weight / last_recalled)。

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
