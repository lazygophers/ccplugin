---
title: 阻塞操作 handler 用 sync def（线程池）
layer: recall
category: impl
keywords: [async,handler,blocking,fastapi]
source: reconstruct
authored-by: skein-spec
created: 1784346009
status: active
related: []
updated: 1784346009
---

## 触发场景
exec 或 config 读取等阻塞操作。

## 陷阺-正解
**陷阺**：async def 内做 subprocess/同步 IO，阻塞事件循环。
**正解**：`def` (sync)，FastAPI 自动跑线程池。

## 规则
skein.py:2272-2273 _exec；:2289 _cfg_get 均 sync def。

## 关联
impl/async-handler-patterns
