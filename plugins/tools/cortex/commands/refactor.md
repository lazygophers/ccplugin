---
description: cortex-refactor 子命令 (dry-run 默认) — 无入参时列建议
---

# /cortex:refactor

[AUTO_MODE strict: 禁询问, fail-fast]

cortex-refactor 操作。

1. 从 `~/.cortex/config.json` 读 vault
2. **若 wrapper 无入参调用 (默认)**: 扫 vault 列重构建议 (top 20):
   - rename 候选 (typo / locale 不一致)
   - merge 候选 (相似 title / overlap > 70%)
   - split 候选 (单文件 > 5KB)
   - dedupe 候选 (相同内容)
   - 输出 plan JSON, **dry-run 不落盘**
3. 若有显式 args: 执行子命令 `rename / merge / split / fold / migrate-locale / restructure / dedupe / extract / inline / graph-rebalance`
   - 默认 dry-run, 仅当 `--apply` 时落盘

输出: plan JSON (候选列表 + 影响范围 + 风险等级)。

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
