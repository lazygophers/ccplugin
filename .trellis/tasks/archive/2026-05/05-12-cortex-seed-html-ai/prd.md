# PRD — cortex seed 模板 HTML 二维化 (AI + 人类双友好)

## 背景

参考:
- [内嵌HTML代替纯Markdown](https://linux.do/t/topic/2142004) — Markdown 锁死垂直轴, HTML 二维布局 token 反更省 (HTML 1275 vs MD 3856)
- [Claude Code 团队成员发文: 是时候用 HTML 替代 Markdown 了](https://linux.do/t/topic/2138856) — Markdown 给大模型表达拖后腿

当前 `presets/seed/` 44 个模板大多是纯 Markdown 线性骨架, 信息密度低, 视觉单调。需重设让 AI 解析友好 + 人类查看舒适。

## 目标

44 模板全部用 HTML grid/flex/card 二维布局, 配 frontmatter (AI 解析) + callout (Obsidian 渲染) + Bases query 占位 (动态视图) + mermaid 图 (流程可视) + `<details>` 折叠 (避免一屏堆叠)。

### 不在范围
- 不动 `_templates/html/*` 片段库 (已建, 仅引用)
- 不动 `_meta/memory-policy.yaml` (无视觉需求)
- 不动 _structure.json (本任务不增减 seed)
- 不动 install SKILL / lint / cron / MCP

## 设计原则

### AI 友好
1. **frontmatter** 严格 schema, AI 直接 parse:
   ```yaml
   ---
   type: index | dashboard | memory-level | root
   title: <人类可读>
   role: <一句话职责>
   namespace: 知识库 | 记忆体系 | 仪表盘 | root
   level: L0-L4   # 仅 memory-level
   children: [...]
   last_updated: {{UPDATED}}
   tags: [...]
   ---
   ```
2. **HTML semantic** — 用 `<section data-role="...">` / `<div data-type="...">` 让 AI 知 region 意图
3. **占位符** `{{VAR}}` 双花括号 — AI 一眼识别需注入数据
4. **Bases query 块** 用 ` ```base ` fenced, 不嵌 HTML 内, AI 可独立解析

### 人类友好
1. **HTML grid 二维** — 3 列卡片网格, 不堆垂直
2. **Callout** — Obsidian `> [!info] / [!tip] / [!warning]` 引导阅读
3. **Emoji icon** — 适度用 (📚 知识库 / 🧠 记忆体系 / 📊 仪表盘 / 🗂️ 归档 / 🔥 热卡)
4. **`<details>`/`<summary>`** — 长内容折叠, 默认展开关键 section
5. **进度条 / badge / 状态色** — 用 inline style (避免依赖 CSS 文件)

### 文件结构 (统一)

每个 `_index.md`:
```markdown
---
<frontmatter>
---

> [!info] {{TITLE}}
> {{ONE_LINE_DESC}}

<section data-role="overview" style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px">
  <div data-type="meta">📁 子目录: {{COUNT}}</div>
  <div data-type="meta">📄 条目: {{ITEM_COUNT}}</div>
  <div data-type="meta">🕐 更新: {{LAST_UPDATED}}</div>
</section>

## 子目录

```base
filters:
  - field: type
    op: eq
    value: index
  - field: path
    op: startswith
    value: "{{CURRENT_PATH}}/"
views:
  - type: cards
```

## 最近条目

<details open>
<summary>近 7 天 (top 10)</summary>

```base
filters:
  - field: path
    op: startswith
    value: "{{CURRENT_PATH}}/"
sort:
  - field: last_updated
    dir: desc
limit: 10
```

</details>

## 相关

- 上级: [[{{PARENT}}]]
- 跨域: {{LINKS}}
```

仪表盘文件结构 (统一):
```markdown
---
type: dashboard
title: {{TITLE}}
view_query: {{BASES_OR_DATAVIEW}}
refresh: weekly | daily | on-demand
---

> [!info] {{TITLE}}
> {{DESC}}

<section data-role="kpi" style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px">
  <div style="padding:12px;background:#f0f7ff;border-radius:8px">
    <div style="font-size:12px;color:#666">总数</div>
    <div style="font-size:24px;font-weight:600">{{TOTAL}}</div>
  </div>
  <!-- 3 more KPI cards -->
</section>

## 视图

```base
{{QUERY}}
```

## 趋势

```mermaid
{{CHART}}
```

## 操作

<div style="display:flex;gap:8px;flex-wrap:wrap">
  <a href="...">🔄 刷新</a>
  <a href="...">📤 导出</a>
</div>
```

主页.md 特殊 (全景仪表盘) — grid 6 区块:
- 焦点 (now) / 热卡 (hot) / 知识库分布 / 记忆 L0-L4 摘要 / cron 状态 / 固化流 mermaid

焦点.md — working set, 极简卡片 list (`<section>` 含 `<article>` 多张焦点卡)

记忆体系 _index (L0-L4) — 加 level-specific badge + policy 摘要:
```markdown
<div style="display:flex;gap:8px;align-items:center">
  <span style="padding:4px 12px;background:#dc2626;color:#fff;border-radius:12px">L0</span>
  <span>核心记忆 · 不可篡改</span>
</div>
```

## 模板分类与改造重点

| 类别 | 数量 | 重点 |
|------|------|------|
| root (主页 + 焦点) | 2 | 全景 grid 6 区, KPI + mermaid + 热卡列表 |
| 仪表盘 | 12 | 统一 KPI 顶 + Bases query 中 + mermaid/图 + 操作底 |
| 记忆体系 _index | 5 | level badge + policy 摘要 + Bases (按 level/uri 过滤) |
| 知识库 顶级 _index | 6 | 子目录 grid + 最近条目 Bases |
| 知识库 来源 子桶 | 4 | host/domain 分组 + Bases query 按 source_kind 过滤 |
| 知识库 领域 7 大类 | 7 | 三级子类 grid (不写三级 _index, 仅父级展示) |
| 知识库 日记 4 时间 | 4 | 时间维度过滤 Bases + 时间线 mermaid |
| 知识库 反思 3 子桶 | 3 | 类型徽章 + 关联 Bases |
| 合计 | 43 | (44 不含 _meta/memory-policy.yaml) |

## 占位符约定 (AI 注入用)

| 占位符 | 含义 |
|--------|------|
| `{{TITLE}}` | 目录/文件中文名 |
| `{{ROLE}}` | 一句话职责 |
| `{{ONE_LINE_DESC}}` | 一句话描述 (callout) |
| `{{CURRENT_PATH}}` | 当前 vault 相对路径 (Bases query 过滤用) |
| `{{PARENT}}` | 上级目录 wikilink |
| `{{COUNT}}` / `{{ITEM_COUNT}}` | 子目录数 / 条目数 |
| `{{LAST_UPDATED}}` | ISO 时间 (install.sh 渲染) |
| `{{LINKS}}` | 跨域 wikilink 列表 |
| `{{TOTAL}}` / `{{KPI_*}}` | 仪表盘 KPI 数据 (cortex-dashboard 注入) |
| `{{QUERY}}` | Bases query 体 |
| `{{CHART}}` | mermaid 图体 |
| `{{LEVEL}}` | L0/L1/L2/L3/L4 |
| `{{LEVEL_COLOR}}` | #dc2626 (L0红) / #ea580c (L1) / #ca8a04 (L2) / #16a34a (L3) / #6b7280 (L4灰) |

## 不预填实际数据

- 所有 `{{VAR}}` 保留占位, 由 `install.sh` 写入时填基础值 (TITLE/CURRENT_PATH/LAST_UPDATED), 其余由 cortex-dashboard skill 运行时填
- `<section data-role>` / `<div data-type>` 永久保留 (是 AI 解析 hint, 非占位)
- Bases query 块的 `value: "{{CURRENT_PATH}}/"` 也是占位, 由 install 替换

## 验收

- [ ] 43 模板全部含 frontmatter + 顶部 callout + HTML grid 二维 + Bases query + 至少 1 个 `<details>` 折叠
- [ ] 所有 `<section>` 用 `data-role`, 所有顶层 `<div>` 用 `data-type` (AI hint)
- [ ] 仪表盘 12 文件含 KPI 顶 + 视图中 + 操作底 三段
- [ ] 记忆体系 5 _index 含 level badge (色按 LEVEL_COLOR 表)
- [ ] 主页.md 含 grid 6 区, 主区均有 `data-role`
- [ ] 焦点.md 是 `<article>` 卡片 list (3-5 张)
- [ ] 占位符全用 `{{}}` 双花括号 (grep 无 single brace 残留)
- [ ] 217 python tests 无回归
- [ ] `_meta/memory-policy.yaml` 不动

## 子任务拆分 (单 wave 并行 ≤2)

| Wave | Agent | 范围 |
|------|-------|------|
| A | A1 trellis-implement | root 2 + 仪表盘 12 + 记忆体系 5 = 19 文件 |
| A | A2 trellis-implement | 知识库 24 _index (顶 6 + 来源 4 + 领域 7 + 日记 4 + 反思 3) |

两 wave 内文件路径互斥, 可并行。

## 风险

| 风险 | 缓解 |
|------|------|
| HTML 内嵌 Obsidian 渲染失败 | 用 inline style, 不依赖 CSS 文件; 验证主流 Obsidian 1.4+ |
| Bases query 语法错误 | 仅占位 `{{QUERY}}`, 不写实际 query, 由 cortex-dashboard 注入 |
| mermaid 不支持 sankey | 用 v10+ syntax, 不行降级 flowchart |
| 占位符太多 install 渲染漏 | install.sh 仅渲染 TITLE/CURRENT_PATH/LAST_UPDATED, 其余 dashboard skill 跑时填 |
