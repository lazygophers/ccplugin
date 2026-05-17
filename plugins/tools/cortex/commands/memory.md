---
description: cortex 记忆生命周期管理 — 无入参跑全量维护 (整理/升级候选/补充/forget 标记/评分); 有 verb 走 CRUD
---

# /cortex:memory

[AUTO_MODE persistent: 禁询问, 自决执行, 禁中止]

记忆自动管理 (默认维护 + CRUD 子命令)。详见 `cortex-memory` skill。

1. 从 `~/.cortex/config.json` 读 vault
2. **若 wrapper 无入参调用 (默认)** — 维护扫 5 阶段:
   - **整理**: uri-index 重建 + frontmatter 校验 + URI 唯一性扫
   - **升级候选**: L4→L3 自动晋 + L3→L2 / L2→L1 / L1→L0 候选写 `记忆/views/candidates.md`
   - **补充 (enrich)**: 弱条目交叉引用 + sessions 例证补 examples / body
   - **forget 标记 (非破坏)**: L3 90d / L2 365d 未召回 → frontmatter `archive_pending: true`, 日志 `记忆/views/alerts.md`
   - **评分双路调**: 召回 + wikilink 反链 → `importance ↑`; 用户反馈 → `confidence ↑↓`
3. 若有显式 args `<verb> <uri> [args...]` — CRUD:
   - read: 渐进披露 (brief → full on demand)
   - write: 按 L<N> 边界/审判规则
   - update: 修订并写 ledger 留痕
   - delete: L0/L1 拒 / L2-L4 标 archive_pending

输出: 维护 JSON 含 5 阶段统计 / CRUD JSON `{ok, mode, uri, data?, error?}`。

> 破坏性操作 (实际归档 / L4 gzip / 腐化删除) 不在本命令内, 由 cron 跑 (memory-archive / memory-compact / memory-warden)。

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
