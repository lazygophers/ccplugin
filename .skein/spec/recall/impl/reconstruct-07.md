---
title: started 首次置定后禁覆盖（幂等）
layer: recall
category: impl
keywords: [idempotent,started,timestamp]
source: reconstruct
authored-by: skein-spec
created: 1784345975
status: active
related: []
updated: 1784345975
---

## 触发场景
重试或重启幂等场景，subtask 已经 started，需要重认领。

## 陷阱-正解
**陷阱**：重认领时覆盖 started 时刻，导致计时错误。
**正解**：started 首次置定后永不覆盖，幂等检查 `if not s.get("started")` 再设。

## 规则
见 skein.py:1419-1420, 1445-1446。

## 关联
impl/idempotent-start-marker
