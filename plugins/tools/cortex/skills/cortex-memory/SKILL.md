---
name: cortex-memory
description: 记忆生命周期管理 — 自动维护 (晋级候选扫 / forget 标记 / 弱条目补充 / weight bump / uri-index 整理) + URI 寻址 CRUD 子命令。无入参跑全量维护; 有 verb 走 CRUD。Triggers on "整理记忆", "维护记忆", "记忆体检", "memory maintain", "记忆写入", "memory write/read/update/delete", "forget", "遗忘".
disable-model-invocation: false
allowed-tools: Bash Read Write Edit Glob mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_list_files_in_dir mcp__obsidian__obsidian_append_content
---

# cortex-memory

[AUTO_MODE persistent: 禁询问, 自决执行, 禁中止]

记忆生命周期管理 — 默认跑维护扫 (非破坏); 有显式 verb 才降级到 CRUD。可独立调用, 也由 `cortex-digest` 阶段 4 委派。

## 触发场景

- 用户显式 "整理记忆" / "维护记忆" / "记忆体检" / "memory maintain" / `/cortex:memory` 无参 → 跑维护
- 用户/AI 显式 CRUD: "记一条" / "memory write/read/update/delete" / "忘了 X" → 走 verb 子命令
- `cortex-digest` 阶段 4 委派 → 跑维护 (其内联 promote-candidates + forget-marker 子集)
- daily cron `memory-promote` / `memory-forget` / `/cortex:forget` → 等价于跑维护 (子集)

## 关键决策树

```
入参为空 / 仅 --vault                → 维护扫 (默认)
入参含 verb=read|write|update|delete → CRUD (走 crud-operations.md)
```

### 维护扫 5 阶段 (默认)

1. **整理** — `~/.cortex/scripts/ledger.sh uri_index_rebuild` 重建 `_meta/uri-index.json`; 校验 frontmatter (level/uri/weight/last_recalled 完整 + URI 全局唯一)
2. **升级候选扫** — 扫 `记忆/L3-短期/episodic/` + `记忆/L2-中期/semantic/`:
   - L4 ledger freq ≥ 3 → 自动 L4→L3 (非候选, 直接晋)
   - L3 freq ≥ 5 + timespan ≥ 3 天 → L3→L2 候选
   - L2 freq ≥ 10 + timespan ≥ 30 天 → L2→L1 候选
   - L1 freq ≥ X (策略文件定) → L1→L0 候选 (标 `needs_user_approval: true`)
   - 落 `记忆/views/candidates.md` (覆写整页), 不自动晋
3. **补充 (enrich)** — 弱条目 (weight < 0.3 或 examples=0) 找知识库交叉引用 + 用户最近 sessions 例证, append 到 frontmatter `examples` / body; 不删原内容
4. **遗忘标记 (forget marker, 非破坏)** — 扫 L2/L3:
   - L3: `now - last_recalled > 90 天` 且 `recall_count < 3` → frontmatter `archive_pending: true`
   - L2: `now - last_recalled > 365 天` 且 `recall_count < 5` → 同上
   - 日志 append `记忆/views/alerts.md ## memory-forget <UTC ISO>` 列 uri 清单
   - 不删不移
5. **评分双路调** — 召回次数 + wikilink 反向引用 → `importance ↑`; 用户 "不对/错了" → `confidence -= 1.0`, "对的" → `confidence += 0.5` (`scripts/cli/lib/evolution.py:update_doc_scores`)

> 破坏性操作 (实际归档 / L4 gzip / 腐化删除) 不在维护扫内, 由独立 cron 跑:
> - `memory-archive` (月 1st 06:00) — archive_pending 落 `归档/forgotten/`
> - `memory-compact` (周日 04:00) — L4 ledger gzip
> - `memory-warden` (1st/15th 05:00) — 腐化检测

### CRUD 子命令 (有 verb 时)

```
verb=read  → 解析 URI → 读 frontmatter + brief (详见 crud-operations.md §read)
verb=write → policy 校验 (L0 拒 / L1 weight≥0.8 / L2 dedupe / L3/L4 自动) → 写 frontmatter + body
verb=update→ 解析 → 校验 immutable_after_confirm → 写回, created 不变
verb=delete→ L0 拒 / L1 force-user / L2-L4 archive_pending=true
```

URI 解析失败 / 路径越界 → 立即拒绝, 不写盘。

## CRUD 输入 (仅 verb≠空 时)

- uri: `L<N>://<path>` (e.g. `L2://semantic/go/goroutine`)
- write/update 需: content (markdown body), `--level`, `--weight` (0.0-1.0), `--recall_when` (string), `--ref` (知识库路径), `--parents`, `--children`
- 可选: `--full` (read 时返回完整 full 字段, 默认仅 brief)

## 输出

### 维护模式 (默认)
```json
{
  "mode": "maintain",
  "indexed": <N>, "invalid_frontmatter": <N>, "duplicate_uri": <N>,
  "promote_candidates_L3_to_L2": <N>, "promote_candidates_L2_to_L1": <N>, "promote_candidates_L1_to_L0": <N>,
  "auto_promoted_L4_to_L3": <N>,
  "enriched": <N>,
  "forget_marked_L2": <N>, "forget_marked_L3": <N>,
  "scores_updated": <N>
}
```

### CRUD 模式
```json
{"ok": true, "mode": "<verb>", "uri": "<u>", "data": {...}}
```

## AUTO_MODE (wrapper / cron 传 `auto` 后缀触发)

- 跳 AskUserQuestion, 按 policy 默认值跳过用户决策处
- persistent: error 自决降级 / 重试, 禁询问, 禁中止
- **特殊拒绝**:
  - L0 write/delete → 一律拒, 输出候选清单, 提示 `~/.cortex/scripts/memory.sh <verb> <uri> --interactive`
  - L1 delete → 一律拒 (同上)

## References (按需加载)

| 文件 | 用途 |
|---|---|
| [`references/crud-operations.md`](references/crud-operations.md) | CRUD 4 verb 详细流程 + URI 解析 + frontmatter 自动填 + 错误处理 |
| [`references/forget.md`](references/forget.md) | forget 标记子流程 (维护阶段 4 详细; daily cron / `/cortex:forget` 触发等价) |
| [`references/scoring.md`](references/scoring.md) | importance / confidence 2 评分字段强制 (lint rule 23) + 启发式 + 衰减规则 |
