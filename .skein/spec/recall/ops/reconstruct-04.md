---
title: 写盘前 diff 检查，内容无变则 skip
layer: recall
category: ops
keywords: [write,incremental,diff,optimization]
source: reconstruct
authored-by: skein-spec
created: 1784345946
status: active
related: []
updated: 1784345946
---

## 触发场景
修改 task.json 或派生文件后，需要持久化，但担心无谓 IO/mtime 抖动影响监控。

## 陷阱-正解
**陷阱**：每次都写，即使内容无变化。
**正解**：写前 diff，内容相同则跳过写，减少 IO 与 mtime 变更。

## 规则
_write_if_changed() 先比对，相同则 skip。

## 关联
data/atomic-write-single-entrance (C7)
