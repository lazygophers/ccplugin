# cortex 仪表盘输出优化 + 模板/skill/prompt 同步

## 目标

12 个仪表盘 seed (`presets/seed/仪表盘/*.md`) 的渲染输出从"占位 callout"升级为**信息密集 + 结构化 + 可读**。同步刷新 `cortex-dashboard` SKILL.md 规范, `scripts/cron/dashboard.sh` prompt, 和数据查询路径。

## 现状问题

| 问题 | 现状 | 期望 |
|------|------|------|
| view_query 类型 | seed 写字符串 (`dashboard-bridge`), skill 期望 dict (`{kind: ..., level: ...}`) | 统一为 dict, seed 全改 |
| 输出结构 | DASH 区只一句"数据待刷新" | KPI 头 + 图表区 + Top-N 表 + 渲染时间戳 |
| 图表类型 | role 描述提及 mermaid sankey/heatmap/mindmap/pie/timeline, 实际渲染时无明确指令 | 每个 dashboard 在 frontmatter 加 `view_chart` (sankey/heatmap/pie/mindmap/timeline/table) |
| KPI 概览 | 无 | 每页顶部 `> [!stats]` callout 一行 (总数 / 新鲜 / 待处理) |
| 说明区 | 无 | 末尾 `<!-- DASH:LEGEND -->` 区 (本图怎么读 + 触发刷新命令) |
| cron prompt | 通用句 "Pick Bases or Dataview" | 改为 `Invoke Skill cortex-dashboard`, SKILL 单一真相 |
| 模板缺 | 无新建 dashboard 的模板 | 加 `presets/seed/_templates/dashboard.md` (已有需校对) |

## 标准化输出结构

每个 dashboard 渲染后 DASH 区结构:

```markdown
<!-- DASH:BEGIN rendered_at=2026-05-13T03:00:00Z query_hash=abc123ef -->

> [!stats] 概览
> **总数** 234 · **本周新增** 12 · **过期 (>30d)** 5 · **晋级候选** 3

### 趋势

```mermaid
<chart-block>
```

### Top 条目

| 标题 | 路径 | weight | 更新 |
|------|------|--------|------|
| ... | [[...]] | 0.85 | 2026-05-12 |

<!-- DASH:LEGEND -->
> [!note] 怎么读
> - 总数: 该层全部 md 计数
> - 晋级候选: weight ≥ 0.7 且未在更高层
>
> 刷新: `bash ~/.cortex/scripts/dashboard.sh` 或 `/cortex:dashboard`

<!-- DASH:END -->
```

各 dashboard 按 role 选择主图表类型, 但 KPI + LEGEND 三件套必出。

## 12 dashboard 方案

| Dashboard | view_chart | KPI 字段 | 主要数据源 |
|-----------|-----------|---------|----------|
| 总览 | grid | KB 总条目 / 记忆总条目 / cron 健康 / 最近活跃 | 全 vault 概览 |
| 知识库分布 | pie | 各领域条目计数 / 占比 / 月增量 | `知识库/<domain>/_index.md` 计数 |
| 知识-记忆 桥接 | sankey | 双向 ref 条目数 / 孤立条目 / 桥接率 | grep `ref:` frontmatter |
| 固化流 | sankey | L4→L3 / L3→L2 / L2→L1 / L1→L0 流量 | `记忆/views/promotion.jsonl` |
| 记忆-L0-核心 | table | L0 总数 / unsealed / sealed | `记忆/L0-核心/*.md` |
| 记忆-L1-长期 | table | L1 总数 / procedural / semantic / 平均 weight | `记忆/L1-长期/*.md` |
| 记忆-L2-中期 | mindmap | L2 节点数 / 网络深度 / 高 weight top | `记忆/L2-中期/*.md` |
| 记忆-L3-短期 | timeline | L3 30d 事件数 / 每日均值 / 峰值日 | `记忆/L3-短期/*.md` |
| 记忆-L4-流水 | heatmap | L4 30d 事件密度 / 总条目 / cli 分布 | `记忆/L4-流水账/sessions/<cli>/...` |
| 记忆-cron 状态 | table | 9 job 状态 / 失败数 / 最近成功 | `~/.cache/cortex/cron/*.{log,json}` |
| 记忆-晋级候选 | table | 候选总数 / by-level / 已批准 / 待人工 | `记忆/views/candidates.md` |
| 记忆-腐化监控 | table | 幻觉率 / 漂移条目 / warden 待审 | `记忆/views/warden.jsonl` |

## 改动清单

### 1. seed 12 页 frontmatter 升级 (`presets/seed/仪表盘/*.md`)

每页加:
- `view_query`: 改 string → dict (`{kind: "memory|knowledge|ledger|cron|bridge|distribution|promotion|warden", level?: "L0|L1|L2|L3|L4", limit?: <int>, window?: "30d|7d|all"}`)
- `view_chart`: `pie|sankey|heatmap|timeline|mindmap|table|grid`
- `view_stale_after`: 小时 (现 skill 默认 24, 显式声明)
- `view_kpi`: list of `{name, source}` (例 `[{name: "总数", source: "count(记忆/L0-核心/*.md)"}, ...]`)
- `view_legend`: 说明文本 (本图怎么读)

每页 body 结构:
```markdown
# {{title}}

> [!info] {{title}}
> {{role}}

<!-- DASH:BEGIN -->
> [!info] 数据待刷新
> 运行 `bash ~/.cortex/scripts/dashboard.sh` 或 `/cortex:dashboard` 后此区将被填充。
<!-- DASH:END -->

<!-- TEMPLATE_END -->
```

### 2. skills/cortex-dashboard/SKILL.md 全面升级

- 输入: view_query (dict) / view_chart / view_kpi / view_legend / view_stale_after
- 渲染输出: KPI callout + 图表 + Top-N 表 + Legend, 全部封闭在 DASH:BEGIN/END
- 数据查询路径 (每 kind 一段, 含具体 Bash 命令示例):
  - `memory`: `find 记忆/<level>-*/**/*.md -type f | wc -l` 等
  - `knowledge`: `find 知识库/<domain>/**/*.md` 或 `bash ~/.cortex/scripts/search.sh --query <q>`
  - `ledger`: `wc -l 记忆/L4-流水账/sessions/<cli>/<YYYY>/<MM>/<DD>/*.jsonl`
  - `cron`: `cat ~/.cache/cortex/cron/*.json` 取 last_run/duration/status
  - `bridge`: `rg "^ref:" 记忆 知识库 --json` aggregate
  - `distribution`: 各 `知识库/<domain>/_index.md` 计数 + 占比
  - `promotion`: `cat 记忆/views/promotion.jsonl` aggregate
  - `warden`: `cat 记忆/views/warden.jsonl` aggregate
- 图表渲染规则 (每 chart 一段 mermaid 模板示例):
  - sankey: `flowchart LR / A -->|N| B / ...`
  - heatmap: `mermaid heatmap` (或退到 markdown table 渲色 emoji)
  - pie: `mermaid pie`
  - timeline: `mermaid timeline`
  - mindmap: `mermaid mindmap`
  - table: 纯 markdown table
  - grid: HTML `<table>` 4 列网格

### 3. cron/dashboard.sh prompt 改造

参考 digest.sh 模式, PROMPT 单行委托:
```
PROMPT="[AUTO_MODE persistent] Invoke Skill cortex-dashboard on vault=$VAULT lang=${LANG_CODE:-zh-CN}. The skill SKILL.md is the single source of truth for query / render / inject. Follow it strictly, no skip, no ask. Emit the compact JSON described in the skill '## 输出' section."
```

### 4. commands/dashboard.md 同步

去除内联 spec, 改成 thin 委托:
```
执行 cortex-dashboard skill (--dry-run/--force/路径 参数透传)。SKILL.md 是单一真相。
```

### 5. presets/seed/_templates/dashboard.md 校对/补全

加完整示例 frontmatter (view_query/chart/kpi/legend/stale_after) 给用户新建 dashboard 时参考。**保留 `lint-skip: true`** (模板豁免)。

### 6. 文档同步

- `docs/_internal/architecture.md`: dashboard 渲染流图同步 (现状若有)
- `skills/cortex-cartographer.md`: 若调 cortex-dashboard, 引用方式同步

## 验收

- 12 seed 全部 frontmatter 含 view_query (dict) / view_chart / view_kpi / view_legend / view_stale_after
- DASH:BEGIN/END 区结构: KPI callout + chart + table + LEGEND 四段
- SKILL.md 含 8 个 kind 的查询命令示例 + 7 个 chart 的渲染模板
- cron/dashboard.sh PROMPT 单行委托 (≤200 字符)
- `bash ~/.cortex/scripts/dashboard.sh --dry-run` 跑通无报错 (mock vault 或现场 vault)
- python tests 全绿 (新加 dashboard 模板结构校验 case)

## 用户确认决策 (2026-05-13)

1. **必须真实数据**: 严禁 `N/A` / `—` / "暂无数据" 占位。SKILL 必须从真实路径查;路径空则计数为 0 (`0` 是真实数据);路径不存在则视为执行错误终止该 dashboard (报 error 在汇总 JSON `errors[]`, 不写 DASH 区, 保留上次渲染)
2. **mermaid fallback 固化**:
   - heatmap → markdown table + emoji 色块 (🟩 0-2 / 🟨 3-5 / 🟧 6-10 / 🟥 >10)
   - sankey → `mermaid flowchart LR` 简化 (L4 -->|N| L3 形式, edge label 写流量)
   - 其余 (pie/mindmap/timeline) 用原生 mermaid 语法 (Obsidian 已支持)
3. **view_query 改 dict**: 12 seed 全部迁移 (现状 string 占位无解析逻辑, 改不破坏)
4. **tags ≥10 强制**: 仪表盘**不再豁免** lint, 12 seed 全部 frontmatter `tags:` 升到 ≥10 (派生维度: `type/dashboard` + `chart/<kind>` + `kind/<query.kind>` + `level/<L>` (若有) + `refresh/<freq>` + `domain/dashboard` + `lang/zh-CN` + `source/seed` + `score/3` + `maturity/stable`)
   - `presets/seed/仪表盘/` 从 lint exemption 列表删
   - `scripts/lint/run.py` 内 dashboard 豁免逻辑同步

## 范围外

- 不动 `cortex-dashboard` 实际渲染代码逻辑 (skill 由 LLM 解读, 无 python 实现)
- 不动 `记忆/views/` 数据生成逻辑 (那是 digest/promote/warden 的产物)
