---
description: 搜索 cortex vault — 多级回退 (hot → index → SC → rg → MCP); 无入参时列最近 10 条
---

# /cortex:search

[AUTO_MODE strict: 禁询问, fail-fast]

在 cortex vault 内搜索内容。

1. 从 `~/.cortex/config.json` 读 vault
2. 若用户提供 query (slash command 后跟参数), 按 cortex-search SKILL 多级回退:
   - hot.md (最近高频) → URI index → semantic 检索 → rg 正则 → MCP obsidian
3. **若无 query (wrapper 无入参调用)**: 列最近 10 条 ledger 事件 (按时间倒序) + vault stats (文件数 / 各 level 计数)

输出: 引用页路径 + 片段 (≤ 200 char)。

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
