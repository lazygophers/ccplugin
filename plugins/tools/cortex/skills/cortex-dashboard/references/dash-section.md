# cortex-dashboard — DASH 区注入结构 + AUTO_MODE 流程

## DASH:BEGIN/END 完整内容

```markdown
<!-- DASH:BEGIN rendered_at=2026-05-13T03:00:00Z query_hash=abc12345 -->

> [!stats] 概览
> **<kpi[0].name>** <val> · **<kpi[1].name>** <val> · **<kpi[2].name>** <val> · **<kpi[3].name>** <val>

### 趋势

<chart-block (mermaid / markdown table / HTML grid)>

### Top 条目

| 标题 | 路径 | weight | 更新 |
|------|------|--------|------|
| ... | [[...]] | 0.85 | 2026-05-12 |

<!-- DASH:LEGEND -->
> [!note] 怎么读
> <view_legend 内容>
>
> 刷新: `bash ~/.cortex/scripts/dashboard.sh` 或 `/cortex:dashboard`

<!-- DASH:END -->
```

**结构强约束**: KPI callout → chart → Top-N table → LEGEND callout, 顺序固定。

`query_hash`: 对 `view_query` dict yaml 化后取 sha256 前 8 位, 用于跳过判定。

## frontmatter 字段表

每页 `仪表盘/<page>.md` frontmatter 必含:

| 字段 | 类型 | 说明 |
|------|------|------|
| `view_query` | dict | `{kind: <enum>, level?: <L0-L4>, limit?: <int>, window?: <30d/7d/all>}` |
| `view_chart` | enum | `pie / sankey / heatmap / timeline / mindmap / table / grid` |
| `view_kpi` | list | `[{name: <str>, source: <bash-expr>}]`, ≥1 ≤6 |
| `view_legend` | str | 图表说明 + 触发刷新命令 |
| `view_stale_after` | int | 小时 (默认 24); now - rendered_at < stale → skip |

CLI 参数:
- `path`: 仪表盘 md 路径; 默认全扫 `仪表盘/*.md`
- `--dry-run`: 仅打印, 不写盘
- `--force`: 忽略 stale_after, 强制重渲

## AUTO_MODE 完整流程 (cron 入口)

`[AUTO_MODE persistent]` 无交互:

1. `Glob "仪表盘/*.md"` (cap 20)
2. 逐页处理:
   a. Read offset=1 limit=60, 解 frontmatter
   b. 缺 view_query / 不是 dict → errors[], skip
   c. 检 DASH:BEGIN rendered_at, < stale_after 且非 --force → skipped++
   d. 按 view_query.kind 跑数据源 Bash (见 data-sources.md)
   e. 数据源路径不存在 → errors[], 不写盘, continue
   f. 渲染 KPI callout + chart + Top-N table + LEGEND → 拼 DASH 区字符串
   g. Edit 替换 DASH:BEGIN..DASH:END 整段 (含区头 rendered_at + query_hash 注释更新)
3. 输出汇总 JSON

**禁**:

- 读 vault 外文件 (~/.cache/cortex/ 例外, 仅 cron kind)
- 读 vault 内任何 .jsonl / .md 全文 (除 frontmatter 前 60 行)
- AskUserQuestion / 中止任何 dashboard 处理
- `N/A` / `—` / "暂无数据" / 占位符

## 输出格式

```
[dashboard] scan 12 pages
  ✅ 仪表盘/总览.md (rendered, 1.4 KiB)
  ⏭️  仪表盘/知识库分布.md (fresh, skipped)
  ❌ 仪表盘/记忆-腐化监控.md (error: 记忆/views/warden.jsonl 不存在)
  ...
{"refreshed": 9, "skipped": 2, "errors": [{"path": "仪表盘/记忆-腐化监控.md", "reason": "记忆/views/warden.jsonl 不存在"}]}
```

JSON 字段:
- `refreshed`: 成功渲染并写盘的路径列表
- `skipped`: 因 stale 跳过的数量 (int)
- `errors`: `[{path, reason}]` 列表
