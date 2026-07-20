---
title: 异步竞态守卫（token 自增去重）
layer: recall
category: frontend
keywords: [concurrency,async,deduplication,race]
source: reconstruct
authored-by: skein-spec
created: 1784346009
status: active
related: []
updated: 1784346009
---

## 触发场景
快速切页或连续搜索，多个异步请求在途。

## 陷阱-正解
**陷阺**：旧响应覆盖新数据。
**正解**：自增 token/lastReq，仅最后一次响应生效，过期响应丢弃。

## 规则
router.js:47-78 navToken；app.js:63-71 lastReq 搜索去重。

## 案例
快速 tab 切换，仅最后 tab 数据渲染；搜索框快速输入，仅最后查询生效。

## 关联
frontend/async-deduplication
