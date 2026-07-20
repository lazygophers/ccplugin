---
title: onLive 软刷订阅（WS 驱动视图重挂）
layer: core
category: frontend
keywords: [websocket,live,refresh,reactive]
source: reconstruct
authored-by: skein-spec
created: 1784345975
status: active
related: []
updated: 1784345975
---

## 触发场景
page 需要订阅数据变化，刷新视图。

## 陷阱-正解
**陷阺**：各 page 自己管理 WS 连接与重挂逻辑。
**正解**：ctx.onLive(remountFn) 订阅数据软刷，router 切页自动退订，page 无需清理。

## 规则
live.js:8 subscribe 返回退订；router.js:62 自动退订。

## 案例
各 page 末尾 `onLive(mountApp)`。

## 关联
frontend/soft-refresh-pattern
