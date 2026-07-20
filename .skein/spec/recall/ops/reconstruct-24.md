---
title: atexit cleanup 校验 port 防误删
layer: recall
category: ops
keywords: [cleanup,singleton,atexit]
source: reconstruct
authored-by: skein-spec
created: 1784346009
status: active
related: []
updated: 1784346009
---

## 触发场景
serve 进程退出时清理 lock 文件。

## 陷阺-正解
**陷阺**：误删他实例的 lock。
**正解**：atexit 清理时校验 lock 内 port == 本进程 port。

## 规则
skein.py:2103-2108 清理；:2112 atexit 注册。

## 关联
ops/singleton-cleanup
