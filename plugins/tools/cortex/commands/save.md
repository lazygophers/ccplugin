---
description: 落档到 cortex vault — 处理 inbox 全部 (无入参) 或写指定 body
---

# /cortex:save

[AUTO_MODE strict: 禁询问, fail-fast]

落档内容到 cortex vault。

1. 从 `~/.cortex/config.json` 读 vault
2. **若 wrapper 无入参调用 (默认)**: 处理 `inbox/` 全部待归档文件:
   - 扫 `inbox/*.md` (cap 20)
   - 每个走 cortex-save SKILL 流程: masking → 推断 kind → 写盘到对应 namespace
   - 处理完移到 `inbox/.processed/<date>/`
3. 若有显式 args (用户在 claude 内调): 按 args 解析 kind/title, body 经 masking 后写盘

输出: 落档文件数 + 各 kind 分布 + 路径列表。

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
