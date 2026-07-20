---
title: HTTP 访问日志统一格式（middleware）
layer: recall
category: ops
keywords: [logging,middleware,monitoring]
source: reconstruct
authored-by: skein-spec
created: 1784346009
status: active
related: []
updated: 1784346009
---

## 触发场景
调试服务问题或审计请求。

## 陷阺-正解
**陷阺**：各处 print，无统一格式。
**正解**：middleware 统一日志格式 `ts method path -> code`，monitor 模式静默。

## 规则
skein.py:2185-2200 middleware；:2004-2006 tty 判断 quiet。

## 关联
ops/logging-standards
