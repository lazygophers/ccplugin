---
title: 批认领 subtask（一次性 claim 整批）
layer: recall
category: impl
keywords: [batch,claim,concurrent,subtask]
source: reconstruct
authored-by: skein-spec
created: 1784345946
status: active
related: []
updated: 1784345946
---

## 触发场景
批量派发 subtask 时，确保整批一次性认领而非逐个 start。

## 陷阱-正解
**陷阱**：逐个 start 各 subtask，每个一回合，窗口内多次发起间隔。
**正解**：`subtask claim` 一次性认领整批，标 running，减少往返 + 消除竞态。

## 规则
see skein.py:1415-1421 (subtask claim 与 claim 对比)。

## 关联
arch/concurrent-write-state-machine (C2), arch/workspace-lock (C1)
