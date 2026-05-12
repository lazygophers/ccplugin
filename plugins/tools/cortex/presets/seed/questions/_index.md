---
type: meta
title: 问题
tags: [meta]
---

# 问题 (Questions)

## 用途

未解决的疑问、待研究方向、开放课题。明确化"我不知道什么"以驱动后续读、问、查。

## 用法

- frontmatter 设 `type: question`, 含 `status: open|closed`, 关闭时加 `answer: [[...]]` 链接答案页
- 一问一笔记, 不要把多个独立问题塞同一页
- 定期 review: 把 closed 移到 archive, 把 stale 改 status 或归并

## 链接

- 上级: [[home]] · [[topics-moc]]
- 相关: [[sources/_index]] · [[concepts/_index]]

```dataview
TABLE status FROM "questions" WHERE !contains(file.path, "_index") SORT status ASC, updated DESC LIMIT 20
```
