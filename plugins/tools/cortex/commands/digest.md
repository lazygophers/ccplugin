---
description: log/session 数据日处理 — 读+析+处+更新+清理+归档 (无入参, 每日 cron)
---

# /cortex:digest

[AUTO_MODE persistent: 禁询问, 自决执行, 禁中止]

每日运行一次完整的 log/session 数据生命周期 (读+析+处+更新+清理+归档):

## 强制流程 (五阶段, 一次跑完)

### 1. 读 (Read)

- `记忆/L4-流水账/ledger/` 近 24h 事件
- `记忆/L4-流水账/sessions/<cli>/<YYYY-MM>/*.jsonl` 近 24h transcript
- `知识库/日记/日/<YYYY-MM>/` 近 24h log 落档
- `知识库/收件箱/*.md` 全量 (fleeting notes 待分类/归档)

### 2. 析 (Analyze)

- 模式聚合: 同事件类型 ≥ 5 → 抽象为 L2 语义候选
- 实体频度: 抽取近 24h 高频 wikilink / tag
- 决策提炼: 含 "决定/决策/选择/采纳" 段落 → 决策候选
- 疑问识别: 含 "?" / "怎么/为何" 段落 → 反思候选

### 3. 处 (Process)

- 生成 `记忆/views/consolidated/<YYYY-MM-DD>.md` 当日摘要 (主题/高频实体/决策清单)
- 反思候选 → `知识库/反思/疑问/<date>-<topic>.md`
- 连接候选 → `知识库/反思/连接/<date>-<a-b>.md`
- 概念候选 → `记忆/views/candidates.md` (待 cortex-promote 审批)
- 收件箱分类: 含可识别主题 (frontmatter `tags` ≥ 2 / wikilinks ≥ 3) → `git mv` 到 `知识库/领域/<topic>/` (合规位置)

### 4. 更新 (Update)

- `MCP cortex_uri_index_rebuild`: 重建 `_meta/uri-index.json`
- `MCP cortex_memory_write`: L4 高频事件升 L3 (frequency ≥ 5 自动)
- 更新 `index.md` / `hot.md` 引用

### 5. 清理 + 归档 (Cleanup + Archive)

- 删 `记忆/L4-流水账/ledger/` 超 30 天且未升 L3 的事件
- 删 `记忆/L3-短期/` 超 90 天且 weight < 0.3 的条目
- 删 `知识库/反思/疑问/` 已被概念化 (反向链接 ≥ 3) 的疑问页
- 收件箱 stub 清理: `知识库/收件箱/*.md` 创建 ≥ 30 天且无入链无 tag → `git rm` (空 stub 不入档)
- 长 log 滚动归档: `知识库/日记/日/<YYYY-MM>/*.md` 中 > 7 天的文件转存到 `folds/<YYYY-QN>.md` (累积到季度桶, idempotent)
- **不动** `记忆/L1-长期/` / `L0-核心/` (高级记忆不自动清)

## 输出

```
date: <YYYY-MM-DD>
read: ledger=<N> sessions=<N> logs=<N> inbox=<N>
analyzed: patterns=<N> entities=<N> decisions=<N> questions=<N>
written: consolidated=<path> candidates=<N> reflection=<N> connection=<N>
updated: uri_index=<N> L4→L3=<N>
cleaned: ledger_purged=<N> L3_purged=<N> questions_purged=<N> inbox_purged=<N> inbox_classified=<N>
```

## 调度

每日 **03:00** cron 自动跑 `~/.cortex/scripts/digest.sh`。
用户手动: `bash ~/.cortex/scripts/digest.sh` 或会话内 `/cortex:digest`。

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
