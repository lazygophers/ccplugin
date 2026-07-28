---
title: observability
layer: recall
category: ops
keywords: [logging,middleware,monitoring,debug,tracing]
status: active
---

## HTTP 访问日志统一格式（middleware）

### 触发场景
调试服务问题或审计请求。

### 陷阱-正解
**陷阱**：各处 print，无统一格式。
**正解**：middleware 统一日志格式 `ts method path -> code`，monitor 模式静默。

### 规则
skein.py:2185-2200 middleware；:2004-2006 tty 判断 quiet。

### 关联
ops/logging-standards

## 关键路径 DBG.log 注入调试追踪

### 触发场景
调试并发/状态问题时启用 SKEIN_DEBUG=1。

### 陷阱-正解
**陷阱**：无追踪，难定位。
**正解**：锁/读写 task/_write_if_changed 等关键点经 DBG.log 注入。

### 规则
skein.py:117/121/226/258/261/1221/1226 示例。

### 关联
ops/debugging
