---
title: 关键路径 DBG.log 注入调试追踪
layer: recall
category: ops
keywords: [logging,debug,tracing]
source: reconstruct
authored-by: skein-spec
created: 1784346009
status: active
related: []
updated: 1784346009
---

## 触发场景
调试并发/状态问题时启用 SKEIN_DEBUG=1。

## 陷阺-正解
**陷阺**：无追踪，难定位。
**正解**：锁/读写 task/_write_if_changed 等关键点经 DBG.log 注入。

## 规则
skein.py:117/121/226/258/261/1221/1226 示例。

## 关联
ops/debugging
