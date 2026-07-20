---
title: 统一 ApiError + page 级错误边界
layer: recall
category: frontend
keywords: [error,exception,handling,boundary]
source: reconstruct
authored-by: skein-spec
created: 1784346009
status: active
related: []
updated: 1784346009
---

## 触发场景
API 请求失败或某 page 渲染失败，需要用户感知但不炸穿整站。

## 陷阱-正解
**陷阺**：异常冒泡，页面崩溃。
**正解**：统一抛 ApiError(status, message)；page render 外层 try/catch 转占位符。

## 规则
api.js:7-23 定义与抛；router.js:73-79 page catch；各 page 内自己 .catch()。

## 关联
frontend/error-boundary
