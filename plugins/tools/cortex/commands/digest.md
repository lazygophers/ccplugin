---
description: log/session 数据日处理 — 读+析+处+更新+清理+归档 (无入参, 每日 cron)
---

# /cortex:digest

[AUTO_MODE persistent: 禁询问, 自决执行, 禁中止]

每日运行一次完整的 log/session 数据生命周期 (读+析+处+更新+清理+归档):

## 强制流程 (五阶段, 一次跑完)

### 1. 读 (Read)

**新增数据 (待处理 + 待消化)**:
- `记忆/L4-流水账/**/*` 任意类型 (md/jsonl/json/yaml/js/ts/sh/py/txt/log), 任意年龄 — 全量
- `知识库/日记/日/<YYYY-MM>/` 全量
- `知识库/收件箱/*.md` 全量 (fleeting notes; ≥30 天强清, <30 天保留)

**既有知识 (用于交叉参照 + 学习更新, 不移除)**:
- `记忆/L0-核心/**` · `L1-长期/**` · `L2-中期/**` · `L3-短期/**` — 全量索引
- `知识库/领域/**` · `知识库/项目/**` · `知识库/来源/**` · `知识库/反思/**` — 全量索引
- `_meta/uri-index.json` · `views/candidates.md` · `views/consolidated/*.md`

**读策略**: 新增 L4 必处理 (分类→归档/删除); 既有 L0-L3 + 知识库参与交叉分析, 数据更新但条目不删。jsonl 按行解析; json/yaml 按结构解析; 其他文本按段落扫。

### 2. 析 (Analyze)

**新增数据**:
- 模式聚合: 同事件类型 ≥ 5 → 抽象为 L2 语义候选
- 实体频度: 抽取高频 wikilink / tag
- 决策提炼: 含 "决定/决策/选择/采纳" 段落 → 决策候选
- 疑问识别: 含 "?" / "怎么/为何" 段落 → 反思候选

**既有知识 vs 新增数据交叉**:
- 命中既有 L1/L2 概念 → 标 `update_target` (待阶段 3 加深)
- 命中既有 知识库/领域 概念 → 标 `enrich_target` (待阶段 3 补例/补连)
- 新事实与既有条目矛盾 → 标 `conflict` (待阶段 3 写反思页)
- 既有疑问页 (`知识库/反思/疑问/`) 反向链接 ≥ 3 → 标 `concretize` (待阶段 5 清理)

### 3. 处 (Process)

**新写**:
- `记忆/views/consolidated/<YYYY-MM-DD>.md` 当日摘要 (主题/高频实体/决策清单)
- 反思候选 → `知识库/反思/疑问/<date>-<topic>.md`
- 连接候选 → `知识库/反思/连接/<date>-<a-b>.md`
- 概念候选 → `记忆/views/candidates.md` (待 cortex-promote 审批)

**更新既有 (学习 + 完善, 不删原文)**:
- `update_target` (L1/L2/L3 命中) → 用 `cortex_memory_write` 追加新例证/新连接/新观察, 提升 weight (+0.05 每次命中, 上限 1.0)
- `enrich_target` (知识库/领域 命中) → patch 文档加 `## 新增例证 <YYYY-MM-DD>` 段, 加 `[[wikilink]]` 入既有概念互联网络
- `conflict` → 新建 `知识库/反思/矛盾/<date>-<topic>.md` 列对照, 不直接改既有条目
- `_meta/uri-index.json` 反向链接计数刷新
- **收件箱强制清空** (≥30 天笔记必处理, 三选一, 无"留在收件箱"选项):
  - **优先 classify**: 用 cortex_search 找最近邻 → 推断主题 → `git mv` 到 `知识库/领域/<topic>/` 或 `知识库/项目/<basename>/`
  - **次选 archive**: 无可识别主题 (cortex_search 无近邻 / tags+wikilinks 为空) → `git mv` 到 `归档/<YYYY>/`
  - **末选 delete**: 仅当文件 ≤ 3 行且无 frontmatter (真 stub) → `git rm`

### 4. 更新 (Update)

- `MCP cortex_uri_index_rebuild`: 重建 `_meta/uri-index.json`
- `MCP cortex_memory_write`: L4 高频事件升 L3 (frequency ≥ 5 自动)
- 更新 `index.md` / `hot.md` 引用

### 5. 清理 + 归档 (Cleanup + Archive)

- **L4-流水账强制全清空** (无时间窗例外): 阶段 1 读取的每个 L4 文件 (任意类型, 任意年龄) 必须出 L4 (三选一):
  - **升 L3**: 高频/有概念化潜力 → `cortex_memory_promote L4→L3`
  - **归档**: 历史价值但无升级潜力 → mv 到 `归档/L4-<YYYY>/<原相对路径>`
  - **删**: 无价值 (debug 噪音/纯重复/已聚合) → `git rm`
  - 处理后 `记忆/L4-流水账/**` 必须 0 文件残留 (digest 是单向漏斗, 不留快照)
- 删 `记忆/L3-短期/` 超 90 天且 weight < 0.3 的条目
- 删 `知识库/反思/疑问/` 已被概念化 (反向链接 ≥ 3) 的疑问页
- 收件箱已在阶段 3 强制清空 (≥30 天必处理), 此阶段仅复核: `知识库/收件箱/` 不应残留 ≥30 天文件
- 长 log 滚动归档: `知识库/日记/日/<YYYY-MM>/*.md` 中 > 7 天的文件转存到 `归档/日记/<YYYY-QN>.md` (累积到季度桶, idempotent)
- **不动** `记忆/L1-长期/` / `L0-核心/` (高级记忆不自动清)

## 输出

```
date: <YYYY-MM-DD>
read: ledger=<N> sessions=<N> logs=<N> inbox=<N> l4_other=<N> existing_L0=<N> existing_L1=<N> existing_L2=<N> existing_L3=<N> existing_kb=<N>
analyzed: patterns=<N> entities=<N> decisions=<N> questions=<N> update_targets=<N> enrich_targets=<N> conflicts=<N> concretize_targets=<N>
written: consolidated=<path> candidates=<N> reflection=<N> connection=<N> conflict=<N>
updated: uri_index=<N> L4→L3=<N> L1_enriched=<N> L2_enriched=<N> L3_enriched=<N> kb_enriched=<N> weights_bumped=<N>
cleaned: l4_promoted=<N> l4_archived=<N> l4_deleted=<N> L3_purged=<N> questions_purged=<N> inbox_classified=<N> inbox_archived=<N> inbox_deleted=<N>
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
