# cortex-digest — 8 阶段 pipeline 详解

> SKILL.md §8 阶段 (一次跑完, 顺序严格) 详细规范。

每阶段开始读 `.cortex/state/<stage>.json` 拿 cursor + processed_files hash 集; 阶段结束写回累计 stats + 新 cursor。state JSON schema 详见 [state-store.md](state-store.md)。

## 1. 读 (Read) 增量扫

**新增数据 (将在阶段 8 清空)**:
- `记忆/L4-流水账/**/*` 任意类型 (md/jsonl/json/yaml/js/ts/sh/py/txt/log) — mtime > `cursors.log_last_date` (首次跑 = 全量)
- `知识库/日记/日/<YYYY-MM>/` mtime > cursor
- `知识库/收件箱/*.md` mtime > `cursors.inbox_last_mtime`

**既有知识 (用于交叉参照 + 学习更新, 永不移除条目)**:
- `记忆/L0-核心/**` · `L1-长期/**` · `L2-中期/**` · `L3-短期/**` 全量索引
- `知识库/领域/**` · `知识库/项目/**` · `知识库/收件箱/**` 全量索引
- `_meta/uri-index.json` · `views/candidates.md` · `views/consolidated/*.md`

**增量跳过**: 计算 sha256, 若 `state/digest.json:processed_files[<rel>].hash` 命中则跳。

**读策略**: jsonl 按行; json/yaml 按结构; 其他按段落。

**输出**: `read.*` 计数 + `read.skipped_by_hash`。

## 2. 析 (Analyze) 深度

LLM 深读全文 (非启发式 keyword 扫), 抽 4 类候选 (反思/连接/矛盾/决策) + 实体 + 概念 + repo 6 信号归属, 标 `update_target` / `enrich_target` / `conflict` / `concretize`。

详见 [extraction.md](extraction.md) §1-§2。

## 3. 处 (Process) 路由

按候选 `route_target` 路由 4 类: 命中 repo → `知识库/项目/<host>/<org>/<repo>/`, 否则 fallback `知识库/收件箱/`; 概念/实体 → `知识库/领域/<域>/` (域名 LLM 自决 / `config/digest.yaml:domain_aliases` 强映射); episodic 高频 → L3。同时更新既有 (weight bump / append 例证, 不删原文)。

详见 [extraction.md](extraction.md) §3。

## 4. 维护 (Maintenance)

### 4a. 知识库引用
- 更新 `index.md` / `hot.md` 引用 (新生 consolidated/reflection 加入索引)

### 4b. 委派 cortex-memory 跑维护扫
调 `Skill(cortex-memory)` 无 verb (默认维护扫), digest 不重复维护逻辑:

1. 整理: uri-index 重建 + frontmatter 校验 + URI 唯一性
2. 升级候选: L4→L3 自动 (freq ≥ 3) + L3→L2 / L2→L1 / L1→L0 候选写 `记忆/views/candidates.md`
3. 补充 (enrich): 弱条目 (weight < 0.3 / examples=0) 交叉引用 + sessions 例证 append
4. forget 标记 (非破坏): L3 90d / L2 365d 未召回 → frontmatter `archive_pending: true`
5. 评分双路调: 召回 + wikilink 反链 → `importance ↑`; 用户反馈 → `confidence ↑↓`

cortex-memory 输出 stats JSON 合并到 digest `updated` 字段。

> 实际归档由独立 `memory-archive` cron (月度 1st 06:00) 执行; L4 ledger gzip 由 `memory-compact` cron (周日 04:00); 腐化检测由 `memory-warden` cron (1st/15th 05:00)。digest 不接管这三类破坏性操作。

## 5. 整合 (Consolidate) — 项目→领域 提炼 (new)

读 `state/consolidate.json` cursor + processed_files hash; 遍历 `知识库/项目/<host>/<org>/<repo>/**` 中 hash 未命中的 md:

1. LLM 深读, 识别**通用概念** (技术/方法/模式, 非项目专属事实)
2. 检查 `知识库/领域/**` 既有概念 — 命中则 patch (append 例证 + 项目 backlink); 未命中则新建 `知识库/领域/<域>/<concept>.md` (frontmatter 含 `type: concept` / `domain` / `aliases` / `sources` 数组列 source 项目路径)
3. 域名决策: `config/digest.yaml:domain_aliases` 强映射优先, 否则 LLM 自决 (技术/创作/学习/工作/生活/金融/未分类)
4. 合并冲突 (与既有概念定义不一致): 落 `知识库/收件箱/<date>-矛盾-<concept>.md` 列对照, 不动既有

阶段结束: hash 写入 `state/consolidate.json:processed_files`, `cursors.last_repo_path` 更新。

详见 [consolidate.md](consolidate.md)。

## 6. 优化 (Enrich) — 图表 + tags/aliases (new)

读 `state/enrich.json` cursor; 遍历 vault 内 hash 未命中的 md (跳过 `_meta/` · `_templates/` · `_assets/` · `.cortex/` · `归档/` · `.obsidian/`):

1. **图表注入**: LLM 判该 md 适合的 mermaid 类型 (流程→flowchart, 时序→timeline, 概念→mindmap, 对比→table); 不适合则跳。注入位置: frontmatter 后、正文前, 加 `## 关系图` 二级标题 + mermaid fence; **不动原正文**。`config/enrich.yaml:mermaid_whitelist` 限制可注入类型。
2. **tags/aliases 重抽**: LLM 抽 ≥3 aliases (中英对) + ≥5 keywords; 与既有 frontmatter `tags` / `aliases` 合并去重 (既有优先, 不删人工写的); `config/tags.yaml:alias_synonyms` 同义词归一

阶段结束: hash 写入 `state/enrich.json:processed_files`。

详见 [enrich.md](enrich.md)。

## 7. 验证 (Verify) — search 多次交叉 (new)

读 `state/verify.json`; 对**高 weight 记忆** (L1/L2 weight ≥ 0.7) + **重要知识库条目** (`领域/**` 含 `score ≥ 7` 或 `importance ≥ 7`) 中 hash 未命中的:

1. 提取 3-5 个不同 keyword 组合 (concept name / aliases / tags)
2. 每组合调 search (优先 `mcp__obsidian__obsidian_simple_search`, 不可达走 ripgrep)
3. 聚合结果, 判:
   - **orphan**: 全部 search 反向无引用 → frontmatter 标 `verify_issue: orphan`
   - **冲突**: search 命中同名概念但定义/score 差异大 → `verify_issue: conflict_<path>`
   - **反向无引用**: 仅自身命中 → `verify_issue: no_backlink`
   - **正常**: 不动 frontmatter

阶段结束: hash 写入 `state/verify.json:processed_files`, 累计 `verify_issues_*` 统计。

详见 [verify.md](verify.md)。

## 8. Evolution + 清理

**8a. Evolution**: 调 `bash ~/.cortex/scripts/digest.sh evolution --lookback-days 7 --json` (直 exec python CLI), 输出 JSON 含 `sessions_scanned` / `patterns_candidates` / `patterns_added` / `patterns_updated` / `proposals_generated`。proposal confidence ≥ 0.8 AND applications ≥ 3 才生。反写 SKILL/AGENT **不在 digest 内自动执行** — 仅生 proposal 列表, 用户调 cortex-refactor `evolution-apply` 单独消化。详见 [evolution.md](evolution.md)。

**8b. 清理 + 归档**: L4 全清 (promote/archive/delete), L3 90d w<0.3 删, 收件箱 ≥30d 复扫识别, 日记 >7d 转季度桶, L0/L1 永不动条目。详见 [cleanup.md](cleanup.md)。

## 输出 (compact JSON)

```json
{
  "date": "<YYYY-MM-DD>",
  "incremental": {
    "state_age_days": <N>, "reset_to_full": <bool>,
    "skipped_by_hash": {"read": <N>, "consolidate": <N>, "enrich": <N>, "verify": <N>}
  },
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
  "consolidate": {
    "scanned": <N>, "concepts_extracted": <N>, "domain_created": <N>, "domain_enriched": <N>, "conflicts_recorded": <N>
  },
  "enrich": {
    "scanned": <N>, "mermaid_injected": <N>, "tags_updated": <N>, "aliases_updated": <N>, "skipped_path": <N>
  },
  "verify": {
    "scanned": <N>, "issues_orphan": <N>, "issues_conflict": <N>, "issues_no_backlink": <N>
  },
  "evolution": {
    "sessions_scanned": <N>, "patterns_added": <N>, "patterns_updated": <N>,
    "proposals_generated": ["<path>"]
  },
  "cleaned": {
    "l4_promoted": <N>, "l4_archived": <N>, "l4_deleted": <N>,
    "L3_purged": <N>, "questions_purged": <N>,
    "inbox_classified": <N>, "inbox_archived": <N>, "inbox_deleted": <N>
  }
}
```

## 阶段间数据流

- 阶段 1 输出文件清单 → 阶段 2 输入
- 阶段 2 输出候选 → 阶段 3 路由
- 阶段 3 写盘 → 阶段 5/6 扫描时纳入
- 阶段 4 维护扫并发于 5-7 (cortex-memory 独立 IO, 不抢锁)
- 阶段 5/6/7 各自独立 state, 互不依赖 (单个失败不影响他者)
- 阶段 8 evolution 输入 L4 sessions (清理前快照), 清理在 8b 紧随其后

## 错误处理

- ledger 行 JSON 解析失败 → 跳过该行, 末尾汇总 invalid_lines count
- session 文件 frontmatter 缺失 → 视为纯文本仅参与 entity 提取
- `views/candidates.md` 不存在 → 自动创建空骨架
- `.cortex/state/<stage>.json` 不存在 / JSON 损坏 → 视为首次跑, 全量重处理 + 重建 state
- `state.last_run` 距今 > `incremental_max_age_days` (默认 30) → 视为首次跑, 全量重处理
- 写盘并发冲突 → 配合 file_lock (cron run.sh 已提供 flock)
- write 失败 → 重试一次, 仍失败则 stderr 报错并继续下一目标 (不中止 pipeline)
- 单阶段 (5/6/7) 失败 → 重试 1 次, 仍失败 stderr 报错继续下一阶段, 该 stage state 不更新 cursor (下次重处理)
