<!-- cortex template: dashboard -->
---
type: dashboard
title: {{TITLE}}
aliases: []
tags: [dashboard, meta]
created: {{CREATED}}
updated: {{UPDATED}}
preset: {{PRESET}}
lang: {{LANG}}
cli: {{CLI}}
cli_session: {{CLI_SESSION}}
refresh: manual   # manual | daily | weekly
template_version: 1
---

# {{TITLE}}

> [!info] 数据来源
> 优先用 Obsidian Bases (1.7+ 核心), Dataview 兜底。本模板预留两套查询块, 二选一保留。

<!-- KPI 卡片: 多列布局 callout 表达不便, 这里保留 HTML grid。 -->

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:8px 0">
  <div style="padding:10px;border-left:3px solid #3b82f6;background:#f0f7ff">
    <strong>总条目</strong><br/><span style="font-size:1.4em">N</span>
  </div>
  <div style="padding:10px;border-left:3px solid #10b981;background:#f0fdf4">
    <strong>本月新增</strong><br/><span style="font-size:1.4em">N</span>
  </div>
  <div style="padding:10px;border-left:3px solid #f59e0b;background:#fff7ed">
    <strong>待发展</strong><br/><span style="font-size:1.4em">N</span>
  </div>
  <div style="padding:10px;border-left:3px solid #ef4444;background:#fef2f2">
    <strong>孤儿页</strong><br/><span style="font-size:1.4em">N</span>
  </div>
</div>

## 视图 — Bases (优先)

<!--
在 Obsidian 1.7+ 推荐用 Bases。在 60_dashboards/<topic>.base 写视图配置, 此处嵌入:
  ![[<topic>.base]]
失败或未启用时, 用下方 Dataview 兜底。
-->

## 视图 — Dataview (兜底)

```dataview
TABLE WITHOUT ID file.link AS "Page", status, updated
FROM "10_concepts"
WHERE status != "stale"
SORT updated DESC
LIMIT 20
```

## 最近更新

```dataview
LIST
FROM "10_concepts" OR "20_entities"
WHERE updated >= date(today) - dur(14 days)
SORT updated DESC
```

## 待办问题

```tasks
not done
tag includes #cortex
```

## 备注

<!-- 维护说明、刷新策略、查询调整记录。 -->

<!-- TEMPLATE_END -->
