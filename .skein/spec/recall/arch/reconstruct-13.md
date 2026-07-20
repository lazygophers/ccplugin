---
title: 服务内部端点用 /__skein__/ 命名空间
layer: recall
category: arch
keywords: [routing,namespace,internal,api]
source: reconstruct
authored-by: skein-spec
created: 1784345975
status: active
related: []
updated: 1784345975
---

## 触发场景
新增后端端点，需要决定命名空间。

## 陷阱-正解
**陷阱**：混用公开与内部路由，路径冲突。
**正解**：内部端点（data/queue/config 等）用 `/__skein__/` 命名空间隔离。

## 规则
skein.py:2008-2010 定义，:2210-2322 所有内部路由一致应用。

## 关联
arch/namespace-isolation
