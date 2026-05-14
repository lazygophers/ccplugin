---
name: cortex-digest
description: log/session 数据日处理 — 读 (含既有 L0-L3 + 知识库) → 析 → 处 (含学习更新) → 更新 → 清理 + 归档。L4 全清单向漏斗, L0/L1 永不删条目。触发: daily cron 03:00 / 用户显式 "digest" / "巩固记忆"。
disable-model-invocation: false
allowed-tools: Bash Read Write Edit Glob Grep Skill
---

# cortex-digest

[AUTO_MODE persistent: 禁询问, 自决执行, 禁中止]

每日运行一次完整的 log/session 数据生命周期 (五阶段), 包含 L4 全清 + 既有知识层交叉学习更新。

## 输入

- `--vault <path>` (必须, 由 wrapper 传入)
- `--lang <code>` (可选, 默认 vault `_meta/version.json:lang` 或 zh-CN)
- `--dry-run` (可选, 仅分析不写盘)

## 五阶段 (一次跑完, 顺序严格)

### 1. 读 (Read)

**新增数据 (将在阶段 5 清空)**:
- `记忆/L4-流水账/**/*` 任意类型 (md/jsonl/json/yaml/js/ts/sh/py/txt/log), 任意年龄 — 全量
- `知识库/日记/日/<YYYY-MM>/` 全量
- `知识库/收件箱/*.md` 全量

**既有知识 (用于交叉参照 + 学习更新, 永不移除条目)**:
- `记忆/L0-核心/**` · `L1-长期/**` · `L2-中期/**` · `L3-短期/**` 全量索引
- `知识库/领域/**` · `知识库/项目/**` · `知识库/收件箱/**` 全量索引
- `_meta/uri-index.json` · `views/candidates.md` · `views/consolidated/*.md`

**读策略**: jsonl 按行解析; json/yaml 按结构解析; 其他文本按段落扫。

### 2. 析 (Analyze)

**新增数据**:
- 模式聚合: 同事件类型 ≥ 5 → 抽象为 L2 语义候选
- 实体频度: 抽取高频 wikilink / tag / 标题关键词
- 决策提炼: 含 "决定/决策/选择/采纳" 段落 → 决策候选
- 疑问识别: 含 "?" / "怎么/为何" 段落 → 反思候选

**新增 vs 既有交叉**:
- 命中既有 L1/L2/L3 概念 → 标 `update_target` (待阶段 3 加深)
- 命中既有 知识库/领域 概念 → 标 `enrich_target` (待阶段 3 补例/补连)
- 与既有条目矛盾 → 标 `conflict` (待阶段 3 写反思页, 不动既有)
- 既有疑问页反向链接 ≥ 3 → 标 `concretize` (待阶段 5 清理)

**repo 归属识别 (反思/连接/矛盾/决策 候选必跑, 6 信号并集, 任一命中即归属)**:

| # | 信号 | 强度 | 示例 |
|---|------|------|------|
| 1 | frontmatter `host` / `org` / `repo` 三字段齐 | 强 | `host: github.com, org: anthropics, repo: claude-code` |
| 2 | frontmatter `source_url` 含 repo 模式 | 强 | `github.com/<org>/<repo>` · `gitlab.*/<org>/<repo>` · `<host>:<port>/<org>/<repo>` |
| 3 | 正文 wikilink `[[知识库/项目/<host>/<org>/<repo>/...]]` 或 `[[<repo-name>]]` 命中已知 repo | 中 | `[[ccplugin]]` 命中 `知识库/项目/persons/lyxamour/ccplugin/` |
| 4 | 正文含 git URL | 中 | `git@github.com:<org>/<repo>.git` · `https://github.com/<org>/<repo>` |
| 5 | tag `repo/<name>` · `host/<host>` · `org/<org>` | 中 | `tags: [repo/ccplugin, org/lyxamour]` |
| 6 | 关键词匹配 `<repo-name>` 出现 ≥ 3 次 (repo 名单从 `知识库/项目/**` 现有目录拉) | 弱 | "ccplugin" 在正文出现 ≥3 次 |

识别结果落候选元数据: `route_target = 知识库/项目/<host>/<org>/<repo>/` (命中) 或 `route_target = inbox` (全无信号)。
多 repo 命中按**强信号优先** (1 > 2 > 3 > 4 > 5 > 6) 选首要 repo, 余者保留为次要 (阶段 3 加 backlink)。

### 3. 处 (Process)

**新写 (按候选 `route_target` 路由, 反思/连接/矛盾/决策 4 类)**:

| 候选类型 | 命中 repo (`route_target` ≠ inbox) | 未命中 (fallback inbox) |
|---|---|---|
| 反思 | `知识库/项目/<host>/<org>/<repo>/笔记/<YYYY-MM-DD>-反思-<topic>.md` | `知识库/日记/日/<YYYY-MM>/<YYYY-MM-DD>-反思-<topic>.md` |
| 连接 | a/b 同 repo: `知识库/项目/<repo>/笔记/<YYYY-MM-DD>-连接-<a-b>.md`; 跨 repo: 落 a 端 (首要), b 端写 backlink (`## 相关` 列 `[[a-side-path]]`) | `知识库/收件箱/<date>-连接-<a-b>.md` |
| 矛盾 | `知识库/项目/<repo>/笔记/<YYYY-MM-DD>-矛盾-<topic>.md` (frontmatter 列既有条目 path) | `知识库/收件箱/<date>-矛盾-<topic>.md` |
| 决策 | `知识库/项目/<repo>/主题/决策.md` append 新段 (文件不存在则新建) | `知识库/收件箱/<date>-决策-<topic>.md` |

其他新写:
- `记忆/views/consolidated/<YYYY-MM-DD>.md` 当日摘要 (主题/高频实体/决策清单)
- 概念候选 → `记忆/views/candidates.md` (待 cortex-promote 审批, **不路由到 项目/**, 记忆层独立)

**路由 fallback 规则**:
- **多 repo 候选**: 路由首要 repo (信号强度: frontmatter > source_url > wikilink > URL > tag > keyword), 其他 repo 各加 backlink 兜底 (b 端 `## 相关` 写 `[[a-side-path]]`)
- **repo 目录不存在** (`知识库/项目/<host>/<org>/<repo>/` 缺): 自动 `mkdir -p`, 同时若 `_index.md` 不存在则建 minimal stub (frontmatter 5 字段: `type: project` / `host` / `org` / `repo` / `created`, body 1 行说明)
- **笔记目录** (`知识库/项目/<repo>/笔记/`) **不存在**: 自动 `mkdir -p`
- **弱信号防误判**: 信号 6 (keyword) 单独命中且无其他强信号 → 不路由, 留 inbox

**更新既有 (学习 + 完善, 不删原文)**:
- `update_target` (L1/L2/L3 命中) → `bash ~/.cortex/scripts/memory.sh write --uri <u> --content <c> --level <l>` append 新例证/新连接, weight += 0.05 (cap 1.0)
- `enrich_target` (知识库/领域 命中) → patch 文件追加 `## 新增例证 <YYYY-MM-DD>` + 加 `[[wikilink]]`
- `conflict` → 新建 `知识库/收件箱/<date>-矛盾-<topic>.md` 列对照 (不直接改既有条目, 待人工分发)

### 4. 更新 (Update)

- `bash ~/.cortex/scripts/ledger.sh uri_index_rebuild`: 重建 `_meta/uri-index.json`
- `bash ~/.cortex/scripts/memory.sh promote --uri <u> --target-level L3`: L4→L3 (frequency ≥ 5 自动)
- 更新 `index.md` / `hot.md` 引用

### 5. 清理 + 归档 (Cleanup + Archive)

- **L4-流水账强制全清** (无时间窗例外, 单向漏斗): 阶段 1 读取的每个 L4 文件必须出 L4 (三选一):
  - **升 L3**: 高频/概念化潜力 → `bash ~/.cortex/scripts/memory.sh promote --uri <u> --target-level L3`
  - **归档**: 历史价值无升级潜力 → mv 到 `归档/L4-<YYYY>/<原相对路径>`
  - **删**: 无价值 (debug 噪音/纯重复/已聚合) → `git rm`
  - 处理后 `记忆/L4-流水账/**` 必须 0 文件残留
- L3-短期: 删 > 90 天且 weight < 0.3
- 知识库/收件箱: 已被概念化 (反向链接 ≥ 3) 的疑问/连接条目 → 删 (已被领域条目吸收)
- 收件箱: 已在阶段 3 强清 (≥30 天必处理); 此阶段复核不残留 ≥30 天文件
- **收件箱 ≥30 天复扫识别 (强制)**: 对 `知识库/收件箱/` 内 mtime ≥ 30 天文件逐一重跑阶段 2 repo 识别 6 信号 — 命中则迁移到 `知识库/项目/<host>/<org>/<repo>/笔记/` (保留原文件名前缀加日期), 仍无命中则归档季度桶 `归档/收件箱-<YYYY-QN>.md` (append, idempotent), 处理后该批 0 残留
- 知识库/日记/日: > 7 天文件转存 `归档/日记/<YYYY-QN>.md` (累积季度桶, idempotent)
- **不动** `记忆/L0-核心` / `L1-长期` 条目 (仅 weight bump 由阶段 3 update_target 处理)

## 输出 (compact JSON)

```json
{
  "date": "<YYYY-MM-DD>",
  "read": {
    "ledger": <N>, "sessions": <N>, "logs": <N>, "inbox": <N>, "l4_other": <N>,
    "existing_L0": <N>, "existing_L1": <N>, "existing_L2": <N>, "existing_L3": <N>, "existing_kb": <N>
  },
  "analyzed": {
    "patterns": <N>, "entities": <N>, "decisions": <N>, "questions": <N>,
    "update_targets": <N>, "enrich_targets": <N>, "conflicts": <N>, "concretize_targets": <N>
  },
  "written": {
    "consolidated": "<path>", "candidates": <N>, "reflection": <N>, "connection": <N>, "conflict": <N>
  },
  "updated": {
    "uri_index": <N>, "L4_to_L3": <N>,
    "L1_enriched": <N>, "L2_enriched": <N>, "L3_enriched": <N>, "kb_enriched": <N>, "weights_bumped": <N>
  },
  "cleaned": {
    "l4_promoted": <N>, "l4_archived": <N>, "l4_deleted": <N>,
    "L3_purged": <N>, "questions_purged": <N>,
    "inbox_classified": <N>, "inbox_archived": <N>, "inbox_deleted": <N>
  }
}
```

## AUTO_MODE 契约

**核心原则**: "禁问" ≠ "中止". AI 必须**自决并执行直至任务完成**。遇歧义按推荐默认值; 工具不熟悉则尝试其他工具组合 (Bash/Edit/Write/MCP/Read 既有样本); 禁报"需人工"/"AI 不会"/"建议后续处理"。

### 严禁

| # | 禁止 |
|---|------|
| 1 | "修复建议"/"建议"/"推荐操作" 章节/表格/列表 |
| 2 | 用户确认问句 (`需确认?`, `是否执行?`, `要继续吗?`, `ok?`, 末尾问号) |
| 3 | AskUserQuestion 调用 (allowed-tools 已禁) |
| 4 | "下一步"/"后续"/"如需"/"可选" 导引 |
| 5 | "需人工"/"待人工"/"建议人工" 推卸辞令 |
| 6 | "AI 能力不足"/"无法自动" 类借口 |
| 7 | 报状态后停 (除非客观失败: 磁盘只读/权限拒绝/git lock) |

### 错误处理

- ledger 行 JSON 解析失败 → 跳过该行, 末尾汇总 invalid_lines count
- session 文件 frontmatter 缺失 → 视为纯文本仅参与 entity 提取
- `views/candidates.md` 不存在 → 自动创建空骨架
- 写盘并发冲突 → 配合 file_lock (cron run.sh 已提供 flock)
- write 失败 → 重试一次, 仍失败则 stderr 报错并继续下一目标 (不中止整个 pipeline)

## 级别边界速查

| level | 边界 | digest 行为 |
|-------|------|------------|
| L0 | 性格/价值观/硬约束, ≤1500c | 仅交叉参照, 永不改 |
| L1 | 技能/稳定语义, ≤5000c | 仅 weight bump + append 新例证 |
| L2 | 语义, ≤3000c, 365 天时效 | weight bump + append; 365 天衰减由 cortex-forget |
| L3 | 情节, ≤2000c, 90 天时效 | append; 90d weight<0.3 删 |
| L4 | ledger/sessions, single-pass | 全清 (promote/archive/delete) |

## 调度

每日 03:00 cron 自动跑 `~/.cortex/scripts/digest.sh` (wrapper) → `/cortex:digest` (slash) → 本 skill。
用户手动: `bash ~/.cortex/scripts/digest.sh` 或会话内 `/cortex:digest`。
