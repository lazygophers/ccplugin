---
type: meta
title: 来源
tags: [meta]
---

# 来源 (Sources)

## 用途

摄取的外部资料: URL、文献、报告、长文。每条 source 保留出处与摄取日期, 供 concepts / entities 引用佐证。

## 用法

- 走 `cortex-ingest <URL>` 或 `cortex-ingest <file>` 抓取并存档
- frontmatter 设 `type: source`, 含 `url` / `author` / `published` / `ingested_at`
- 不直接消费 source 长文 — 抽要点回填到 concepts / questions

## 链接

- 上级: [[home]] · [[topics-moc]]
- 相关: [[concepts/_index]] · [[questions/_index]]

```dataview
TABLE url, ingested_at FROM "sources" WHERE !contains(file.path, "_index") SORT ingested_at DESC LIMIT 20
```
