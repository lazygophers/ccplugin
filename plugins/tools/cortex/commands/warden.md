---
description: 跑腐化检测 — 扫记忆/知识库一致性 (无入参)
---

# /cortex:warden

[AUTO_MODE strict: 禁询问, fail-fast, 仅读不写]

跑 cortex vault 腐化检测:

1. 从 `~/.cortex/config.json` 读 vault
2. 扫双 namespace 一致性: 记忆 ↔ 知识库交叉引用
3. 检测 frontmatter 字段缺失 / 类型错误
4. 检测 wiki-link 死链
5. 检测重复 title (同 namespace 内冲突)
6. 检测 weight / freq 异常 (突增/突降)

输出: 腐化等级报告 (✗ corrupted / ⚠ suspect / ✓ healthy) + 修复建议。

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
