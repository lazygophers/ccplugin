---
title: middleware 缓存 request body 供 handler 复用
layer: recall
category: impl
keywords: [middleware,request,caching,stream]
source: reconstruct
authored-by: skein-spec
created: 1784346009
status: active
related: []
updated: 1784346009
---

## 触发场景
多个 handler 或中间件需要读 request body。

## 陷阱-正解
**陷阺**：body stream 一次性，重复读失败。
**正解**：middleware 读一次缓存进 request.scope["skein_body"]，handler 复用不重读。

## 规则
skein.py:2185-2200 middleware；:2260/:2275/:2297 handler 取用。

## 关联
impl/request-caching
