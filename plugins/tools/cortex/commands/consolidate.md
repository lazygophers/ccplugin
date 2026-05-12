---
description: 跑 ledger → views 周报巩固 + 反思生成 (无入参, 默认上周)
---

# /cortex:consolidate

[AUTO_MODE strict: 禁询问, fail-fast]

按 cortex-consolidate SKILL 流程跑周报巩固 (默认上周, ISO 周号):

1. 从 `~/.cortex/config.json` 读 vault, cd 进入
2. 扫 `L4/ledger/<week>/*.md` 抽取事件
3. 模式聚合 (同事件类型 ≥ 5 → 抽象为 L2 候选)
4. 生成 `views/consolidated/<week>.md` 周报 (主题分布 / 高频实体 / 反思洞察)
5. 触发 cortex-promote 子流程: 写晋级候选到 `views/candidates.md`

输出: 生成的 views 文件路径 + 主题统计 + 候选数。

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
