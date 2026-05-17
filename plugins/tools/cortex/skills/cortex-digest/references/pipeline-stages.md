# cortex-digest — 六阶段 pipeline 详解

> SKILL.md §六阶段 (一次跑完, 顺序严格) 详细规范。

## 1. 读 (Read)

**新增数据 (将在阶段 5 清空)**:
- `记忆/L4-流水账/**/*` 任意类型 (md/jsonl/json/yaml/js/ts/sh/py/txt/log), 任意年龄 — 全量
- `知识库/日记/日/<YYYY-MM>/` 全量
- `知识库/收件箱/*.md` 全量

**既有知识 (用于交叉参照 + 学习更新, 永不移除条目)**:
- `记忆/L0-核心/**` · `L1-长期/**` · `L2-中期/**` · `L3-短期/**` 全量索引
- `知识库/领域/**` · `知识库/项目/**` · `知识库/收件箱/**` 全量索引
- `_meta/uri-index.json` · `views/candidates.md` · `views/consolidated/*.md`

**读策略**: jsonl 按行解析; json/yaml 按结构解析; 其他文本按段落扫。

## 2. 析 (Analyze)

抽 4 类候选 (反思/连接/矛盾/决策) + 跑 repo 归属识别 (6 信号并集), 标 `update_target` / `enrich_target` / `conflict` / `concretize`。

详见 [extraction.md](extraction.md) §1-§2。

## 3. 处 (Process)

按候选 `route_target` 路由 4 类 (反思/连接/矛盾/决策), 命中 repo 落 `知识库/项目/<host>/<org>/<repo>/`, 否则 fallback `知识库/收件箱/`。同时更新既有 (weight bump / append 例证, 不删原文)。

详见 [extraction.md](extraction.md) §3。

## 4. 更新 (Update)

### 4a. 知识库引用
- 更新 `index.md` / `hot.md` 引用 (新生 consolidated/reflection 加入索引)

### 4b. 委派 cortex-memory 跑维护扫
调 `Skill(cortex-memory)` 无 verb (默认维护扫), digest 不再重复维护逻辑 — 由 cortex-memory 作为单一真相源跑:

1. 整理: uri-index 重建 + frontmatter 校验 + URI 唯一性
2. 升级候选: L4→L3 自动 (freq ≥ 3) + L3→L2 / L2→L1 / L1→L0 候选写 `记忆/views/candidates.md`
3. 补充 (enrich): 弱条目 (weight < 0.3 / examples=0) 交叉引用 + sessions 例证 append
4. forget 标记 (非破坏): L3 90d / L2 365d 未召回 → frontmatter `archive_pending: true`, 日志 `记忆/views/alerts.md`
5. 评分双路调: 召回 + wikilink 反链 → `importance ↑`; 用户反馈 → `confidence ↑↓`

cortex-memory 输出的统计 JSON 合并到 digest 的 `updated` 字段 (`promote_candidates_*` / `forget_marked_*` / `enriched` / `scores_updated`)。

详见 `skills/cortex-memory/SKILL.md §维护扫 5 阶段`。

> 实际归档由独立 `memory-archive` cron (月度 1st 06:00) 执行; L4 ledger gzip 由 `memory-compact` cron (周日 04:00); 腐化检测由 `memory-warden` cron (1st/15th 05:00)。digest + cortex-memory 维护均不接管这三类破坏性操作。

## 5. 清理 + 归档 (Cleanup + Archive)

L4-流水账强制全清 (单向漏斗: promote/archive/delete), L3 > 90 天 weight<0.3 删, 收件箱 ≥30 天复扫识别, 日记 > 7 天转季度桶, L0/L1 永不动条目。

详见 [cleanup.md](cleanup.md)。

## 6. Evolution (经验抽取 → semantic 模式库 + 反写提议)

调 `bash ~/.cortex/scripts/digest.sh evolution --lookback-days 7 --json` (直接 exec python CLI, 不走 slash) 获取 JSON 输出, 含:

- `sessions_scanned`: 扫描的 session jsonl 文件数
- `patterns_candidates`: 候选 pattern 数 (`applications ≥ 3`)
- `patterns_added`: 新写入 `记忆/L0-核心/patterns.md` 的 pattern 数
- `patterns_updated`: 既有 pattern applications +1 的数
- `proposals_generated`: 落 `_assets/evolution-proposals/` 的 proposal 文件路径列表 (confidence ≥ 0.8 AND applications ≥ 3 才生)

详见 [evolution.md](evolution.md)。

**反写 SKILL/AGENT 不在 digest 流程内自动执行** — 仅生 proposal 列表。用户主动调 cortex-refactor 或下次 cortex-digest 跑时通过 AskUserQuestion 单次确认 → patch。

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
    "L1_enriched": <N>, "L2_enriched": <N>, "L3_enriched": <N>, "kb_enriched": <N>, "weights_bumped": <N>,
    "promote_candidates_L3_to_L2": <N>, "promote_candidates_L2_to_L1": <N>, "promote_candidates_L1_to_L0": <N>,
    "forget_marked_L2": <N>, "forget_marked_L3": <N>
  },
  "cleaned": {
    "l4_promoted": <N>, "l4_archived": <N>, "l4_deleted": <N>,
    "L3_purged": <N>, "questions_purged": <N>,
    "inbox_classified": <N>, "inbox_archived": <N>, "inbox_deleted": <N>
  }
}
```

## 错误处理

- ledger 行 JSON 解析失败 → 跳过该行, 末尾汇总 invalid_lines count
- session 文件 frontmatter 缺失 → 视为纯文本仅参与 entity 提取
- `views/candidates.md` 不存在 → 自动创建空骨架
- 写盘并发冲突 → 配合 file_lock (cron run.sh 已提供 flock)
- write 失败 → 重试一次, 仍失败则 stderr 报错并继续下一目标 (不中止整个 pipeline)
