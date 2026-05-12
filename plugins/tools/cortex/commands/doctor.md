---
description: 跑 cortex 健康检查 — vault/config/links/dead-links (无入参)
---

# /cortex:doctor

[AUTO_MODE strict: 禁询问, fail-fast, 仅读不写]

按 cortex-doctor SKILL 流程跑健康检查:

1. 从 `~/.cortex/config.json` 读 vault 与 install_path
2. 检查 vault 结构 (双 namespace / seed 文件 / _meta)
3. 扫死链 (\[\[wiki-link\]\]) 与孤儿文件
4. 校验 frontmatter (kind / locale / last_updated)
5. 报告 config / links / dead-links / 路径异常

输出: 可读分级报告 (✗ critical / ⚠ warning / ✓ healthy)。

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
