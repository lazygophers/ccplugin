---
type: meta
title: 仪表盘
tags: [meta]
---

# 仪表盘 (Dashboards)

## 用途

Dataview / Bases 聚合视图集合。每个 dashboard 是一个可视化切面 (近期更新、待办问题、未引用孤儿等),用于 vault 健康度巡检。

## 用法

- 新建 dashboard 时 `type: dashboard`, 用 dataview / bases 查询块组装
- 命名按主题: `recent-updates.md`, `orphans.md`, `open-questions.md` 等
- 复杂查询走 `_templates/dashboard.md` 起手

## 链接

- 上级: [[home]]
- 入口: [[../dashboard]] (vault 根聚合) · [[../index]]

```dataview
LIST FROM "dashboards" WHERE !contains(file.path, "_index") SORT updated DESC LIMIT 20
```
