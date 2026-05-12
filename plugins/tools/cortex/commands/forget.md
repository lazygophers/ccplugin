---
description: 跑遗忘扫描 — 低权重/过期记忆移到归档 tombstone (无入参)
---

# /cortex:forget

[AUTO_MODE persistent: 禁询问, 自决执行, 禁中止]

按 cortex-forget SKILL 流程跑遗忘扫描:

1. 从 `~/.cortex/config.json` 读 vault
2. 扫 L3/L2 记忆: weight < 阈值 (见 `_meta/memory-policy.yaml`) 且 last_recalled 超期
3. 候选 → 移到 `归档/forgotten/<date>/` 留 tombstone (保留 URI + 简要)
4. 写 ledger 留痕 (forget 事件)
5. L0/L1 受保护永不遗忘

输出: 遗忘候选列表 + 移除文件数 + tombstone 路径。

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
