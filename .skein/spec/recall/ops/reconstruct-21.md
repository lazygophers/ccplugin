---
title: serve 缺依赖动态装 (pip install)
layer: recall
category: ops
keywords: [dependency,lazy,optional,serve]
source: reconstruct
authored-by: skein-spec
created: 1784346009
status: active
related: []
updated: 1784346009
---

## 触发场景
serve 启动前，fastapi/uvicorn 可能未装。

## 陷阺-正解
**陷阺**：import 炸，无 fallback。
**正解**：serve 前检查依赖，缺则 pip 装，仍缺则告警 stderr 返回错误码。

## 规则
skein.py:2034-2045 检查函数；:2085-2092 装与告警。

## 关联
ops/optional-dependencies
