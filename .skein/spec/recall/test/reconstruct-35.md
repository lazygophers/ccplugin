---
title: CLI 测试：subprocess 端到端（非 import 白盒）
layer: recall
category: test
keywords: [test,integration,subprocess,e2e]
source: reconstruct
authored-by: skein-spec
created: 1784346042
status: active
related: []
updated: 1784346042
---

## 触发场景
编写 skein CLI 测试。

## 陷阺-正解
**陷阺**：import 白盒测试，mock 过度。
**正解**：subprocess 跑真实 skein.py + tmp 仓/git，端到端集成。

## 案例
test_skein.py:22-27 / test_board.py:150-162。
