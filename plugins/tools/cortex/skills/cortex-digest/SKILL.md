---
name: cortex-digest
description: log/session 数据日处理 — 读 (含既有 L0-L3 + 知识库) → 析 → 处 (含学习更新) → 更新 → 清理 + 归档。L4 全清单向漏斗, L0/L1 永不删条目。触发: daily cron 03:00 / 用户显式 "digest" / "巩固记忆"。
disable-model-invocation: false
allowed-tools: Bash Read Write Edit Glob Grep Skill
---

# cortex-digest

[AUTO_MODE persistent: 禁询问, 自决执行, 禁中止]

每日运行一次完整的 log/session 数据生命周期 (六阶段), 包含 L4 全清 + 既有知识层交叉学习更新 + evolution 经验抽取 (semantic 模式库 + 反写提议)。

## 输入

- `--vault <path>` (必须, 由 wrapper 传入)
- `--lang <code>` (可选, 默认 vault `_meta/version.json:lang` 或 zh-CN)
- `--dry-run` (可选, 仅分析不写盘)

## 六阶段 (一次跑完, 顺序严格)

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

抽 4 类候选 (反思/连接/矛盾/决策) + 跑 repo 归属识别 (6 信号并集), 标 `update_target` / `enrich_target` / `conflict` / `concretize`。

详见 [references/extraction.md](references/extraction.md) §1-§2。

### 3. 处 (Process)

按候选 `route_target` 路由 4 类 (反思/连接/矛盾/决策), 命中 repo 落 `知识库/项目/<host>/<org>/<repo>/`, 否则 fallback `知识库/收件箱/`。同时更新既有 (weight bump / append 例证, 不删原文)。

详见 [references/extraction.md](references/extraction.md) §3。

### 4. 更新 (Update)

- `bash ~/.cortex/scripts/ledger.sh uri_index_rebuild`: 重建 `_meta/uri-index.json`
- `bash ~/.cortex/scripts/memory.sh promote --uri <u> --target-level L3`: L4→L3 (frequency ≥ 5 自动)
- 更新 `index.md` / `hot.md` 引用

### 5. 清理 + 归档 (Cleanup + Archive)

L4-流水账强制全清 (单向漏斗: promote/archive/delete), L3 > 90 天 weight<0.3 删, 收件箱 ≥30 天复扫识别, 日记 > 7 天转季度桶, L0/L1 永不动条目。

详见 [references/cleanup.md](references/cleanup.md)。

### 6. Evolution (经验抽取 → semantic 模式库 + 反写提议)

调 `bash ~/.cortex/scripts/digest.sh evolution --lookback-days 7 --json` (直接 exec python CLI, 不走 slash) 获取 JSON 输出, 含:

- `sessions_scanned`: 扫描的 session jsonl 文件数
- `patterns_candidates`: 候选 pattern 数 (`applications ≥ 3`)
- `patterns_added`: 新写入 `记忆/L0-核心/patterns.md` 的 pattern 数
- `patterns_updated`: 既有 pattern applications +1 的数
- `proposals_generated`: 落 `_assets/evolution-proposals/` 的 proposal 文件路径列表 (confidence ≥ 0.8 AND applications ≥ 3 才生)

详见 [references/evolution.md](references/evolution.md)。

**反写 SKILL/AGENT 不在 digest 流程内自动执行** — 仅生 proposal 列表。用户主动调 cortex-refactor 或下次 cortex-digest 跑时通过 AskUserQuestion 单次确认 → patch (PR4 范围)。

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
| L2 | 语义, ≤3000c, 365 天时效 | weight bump + append; 365 天衰减由 cortex-memory forget 子流程 |
| L3 | 情节, ≤2000c, 90 天时效 | append; 90d weight<0.3 删 |
| L4 | ledger/sessions, single-pass | 全清 (promote/archive/delete) |

## 调度

每日 03:00 cron 自动跑 `~/.cortex/scripts/digest.sh` (wrapper) → `/cortex:digest` (slash) → 本 skill (会在阶段 6 内联调 `digest.sh evolution` 抽 pattern)。
用户手动: `bash ~/.cortex/scripts/digest.sh` 或会话内 `/cortex:digest`。
evolution 单独跑: `bash ~/.cortex/scripts/digest.sh evolution --lookback-days 7 --json` (直调 python CLI, 不走 claude session)。
