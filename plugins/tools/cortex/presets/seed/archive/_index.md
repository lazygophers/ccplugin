---
type: meta
title: 归档
tags: [meta]
---

# 归档 (Archive)

## 用途

过时、已合并、被取代的内容保留地。不删除以保留历史,但从主流导航撤出,避免污染搜索/dataview。

## 用法

- 手动 mv 笔记到此, 或被 `cortex-historian` 自动归档
- 归档前加 frontmatter `archived_at` + `reason` (superseded / merged / stale)
- 需要恢复: mv 回原目录, 删 `archived_at` 字段

## 链接

- 上级: [[home]]
- 来源: [[fleeting/_index]] · [[questions/_index]] (closed)

```dataview
TABLE archived_at, reason FROM "archive" WHERE !contains(file.path, "_index") SORT archived_at DESC LIMIT 20
```
