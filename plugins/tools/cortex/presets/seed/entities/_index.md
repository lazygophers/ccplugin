---
type: meta
title: 实体
tags: [meta]
---

# 实体 (Entities)

## 用途

具体可指代的对象: 人、组织、产品、工具、服务。区别于 concepts 的抽象性,entities 必有现实指代物。

## 用法

- frontmatter 设 `type: entity`, 必填 `alias` / `url` (官方主页) / `entity_type` (person/org/product/tool)
- 同一实体不同别名: 用 `aliases: [...]` 聚合, 避免重复笔记
- 与 concept 关联 → 在 concept 笔记内 wikilink 引用此 entity

## 链接

- 上级: [[home]] · [[topics-moc]]
- 相关: [[concepts/_index]] · [[domains/_index]]

```dataview
TABLE entity_type, url FROM "entities" WHERE !contains(file.path, "_index") SORT updated DESC LIMIT 20
```
