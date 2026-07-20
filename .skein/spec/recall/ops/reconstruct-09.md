---
title: 删除 task 软删入 trash（可恢复）
layer: recall
category: ops
keywords: [delete,soft-delete,trash,recovery]
source: reconstruct
authored-by: skein-spec
created: 1784345975
status: active
related: []
updated: 1784345975
---

## 触发场景
删除 task 或旧看板日志。

## 陷阱-正解
**陷阱**：直接 rm，不可恢复。
**正解**：软删入 .skein/trash/<id>.<YYYYMMDD>/，可恢复; 单 subtask 直接删。

## 规则
skein.py:186 定义 trash 路径；:673/:697-711 软删逻辑。

## 关联
ops/soft-delete-restore
