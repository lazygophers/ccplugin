---
title: hover popover 状态机（fixed 定位 + getBoundingClientRect）
layer: recall
category: frontend
keywords: [popover,hover,positioning,state-machine]
source: reconstruct
authored-by: skein-spec
created: 1784346093
status: active
related: []
updated: 1784346093
---

## 触发场景
DAG 节点悬浮浮层。

## 陷阳-正解
**陷阺**：浮层被 overflow 裁剪。
**正解**：has-tip[data-tip] / .dag-tip[data-for] 配对；position:fixed 逃逸；mouseenter/leave 切显隐；下方放不下翻上方。

## 规则
board/switcher.js:138-155 完整实现。
