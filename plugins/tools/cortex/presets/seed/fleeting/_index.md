---
type: meta
title: 临时笔记
tags: [meta]
---

# 临时笔记 (Fleeting)

## 用途

瞬时想法的收件箱: 未整理、未分类、未链接的快速捕获。零摩擦写入,后续 fold / archive。

## 用法

- frontmatter 仅需 `type: fleeting` + `created`,其它可省
- 定期跑 `cortex-historian fold` 自动归并到 concepts / questions
- 或手动审阅: 有价值的提升为正式笔记, 无价值的移 archive

## 链接

- 上级: [[home]]
- 流向: [[concepts/_index]] · [[questions/_index]] · [[archive/_index]]

```dataview
LIST FROM "fleeting" WHERE !contains(file.path, "_index") SORT created DESC LIMIT 30
```
