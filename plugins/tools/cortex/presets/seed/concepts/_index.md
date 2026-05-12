---
type: meta
title: 概念
tags: [meta]
---

# 概念 (Concepts)

## 用途

抽象知识单元的聚合地: 理论、模式、术语、原则。每条 concept 应是 atomic (单一焦点),可被其它笔记 wikilink 引用。

## 用法

- 新建 concept note 时, frontmatter 设 `type: concept`, 加 `aliases` 便于双链
- 内容聚焦"是什么 / 为何重要 / 与谁相关",细节走 entities/sources
- 完成后回链 [[topics-moc]] 入主题地图

## 链接

- 上级: [[home]] · [[topics-moc]]
- 相关: [[entities/_index]] · [[sources/_index]]

```dataview
LIST FROM "concepts" WHERE !contains(file.path, "_index") SORT updated DESC LIMIT 20
```
