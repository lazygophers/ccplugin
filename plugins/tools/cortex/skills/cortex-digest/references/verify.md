# Verify — 阶段 7 search 多次交叉验证

> cortex-digest 8 阶段 §7 详细规范。新阶段 (PR digest-deep)。

对高 weight 记忆 / 重要知识库条目, 用多组关键词跑 search, 检测 orphan / 冲突 / 反向无引用, 落 `verify_issue` frontmatter 标记 (非破坏)。

## 输入

- state: `vault/.cortex/state/verify.json`
- 扫描范围 (二选一即纳入):
  - **高 weight 记忆**: `记忆/L1-长期/**` · `L2-中期/**` 中 `weight ≥ 0.7` 或 `importance ≥ 7`
  - **重要知识库**: `知识库/领域/**` 中 `score ≥ 7` 或 `importance ≥ 7`
- hash 命中 `processed_files` 跳过

## 算法

```
for each entry in scan_targets:
  if hash in processed_files: skip
  kw_combos = build_keyword_combos(entry)   # 3-5 组不同关键词
  results = []
  for combo in kw_combos:
    r = search(combo, scope="vault")        # 优先 mcp__obsidian__obsidian_simple_search
    results.append((combo, r))
  issue = diagnose(entry, results)
  if issue:
    patch frontmatter: verify_issue: <issue>, verify_checked_at: <UTC>
  写 hash 到 state/verify.json
```

## keyword combo 构造

- combo 1: concept name (规范名)
- combo 2: 主要 alias (从 frontmatter `aliases[0]`)
- combo 3: name + 首个 tag (AND)
- combo 4 (可选): 英文 alias 单独
- combo 5 (可选): 反向 — 用 entry 内容中 1 个高频实体反查

去重: combo 完全相同则合并。

## diagnose 规则

| 条件 | issue |
|---|---|
| 5 combo 全部无任何反向链接 (`[[<entry_name>]]` 引用本条) | `orphan` |
| 命中同名 / 同 alias 概念但 score 差 ≥ 3 或 definition LLM 判矛盾 | `conflict_<conflicting_path>` |
| 仅自身命中 (search 结果只有 entry 自己) | `no_backlink` |
| 无问题 | (不写 verify_issue, 清除既有 verify_issue 字段) |

多 issue 时按优先级取首要: `conflict > orphan > no_backlink`。

## frontmatter patch

```yaml
verify_issue: orphan   # 或 conflict_<path> 或 no_backlink
verify_checked_at: <UTC ISO>
verify_combos: 5       # 跑了几组关键词
```

**正常情况** (无 issue) 也写 `verify_checked_at` 但**不**写 verify_issue, 同时**删除**既有 verify_issue 字段 (修复后清标)。

## search 工具优先级

1. `mcp__obsidian__obsidian_simple_search(query, vault)` — 优先, 索引快
2. `mcp__obsidian__obsidian_complex_search(filter)` — combo 含 tag 限定时用
3. `bash ~/.cortex/scripts/search.sh <query>` — MCP 不可达
4. ripgrep — 兜底 (`rg -l "<term>" <vault>`)

## 输出统计

```json
{
  "scanned": <N>,
  "issues_orphan": <N>,
  "issues_conflict": <N>,
  "issues_no_backlink": <N>,
  "issues_cleared": <N>
}
```

## 问题分级 (后续处理参考)

| issue | 严重度 | 建议处理 (人工 / 下次 digest) |
|---|---|---|
| `conflict_*` | 高 | 人工审 collusion, 落 `知识库/收件箱/<date>-矛盾-*.md` |
| `orphan` | 中 | 可能是孤岛知识, digest 下次跑 enrich 时尝试加 backlink |
| `no_backlink` | 低 | 自然现象 (新条目), 多跑几次 digest 会自然补 |

**digest 本阶段不自动修复 issue** — 仅标记, 留给后续阶段或人工。

## 性能

- 单 entry 3-5 次 search; 200 个高 weight entry → ~ 600-1000 search 调用
- 优先 MCP (内存索引快), 慢路径 ripgrep
- 增量 hash 保证未改条目下次跳过

## 失败处理

- 单 search 调用失败 → 跳该 combo, 不算入有效结果
- 5 combo 全失败 → 跳该 entry, 不写 hash (下次重试)
- frontmatter patch 失败 → stderr 报 warn, 不算 issue 已处理
