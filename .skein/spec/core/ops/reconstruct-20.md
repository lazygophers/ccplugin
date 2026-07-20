---
title: subprocess 设 timeout/cwd/capture_output
layer: core
category: ops
keywords: [subprocess,safety,timeout,isolation]
source: reconstruct
authored-by: skein-spec
created: 1784346009
status: active
related: []
updated: 1784346009
---

## 触发场景
exec 端点运行白名单命令。

## 陷阺-正解
**陷阺**：子进程无限卡、无输出捕获、路径污染。
**正解**：timeout=60 超时，cwd=root 隔离，capture_output=True 捕获。

## 规则
skein.py:2282-2287 完整示例。

## 关联
ops/subprocess-safety
