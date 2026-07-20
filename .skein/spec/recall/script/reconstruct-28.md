---
title: CLI 输出走 rich Console（非裸 print）
layer: recall
category: script
keywords: [cli,output,rich,console]
source: reconstruct
authored-by: skein-spec
created: 1784346042
status: active
related: []
updated: 1784346042
---

## 触发场景
用户可见输出（表格、面板、进度)。

## 陷阺-正解
**陷阺**：裸 print。
**正解**：经 rich.console.Console (全仓 221 处示例)。
