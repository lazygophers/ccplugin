---
title: events
layer: recall
category: frontend
keywords: [event,delegation,dom,pattern,popover,hover,positioning,state-machine]
status: active
---

## document click 委托 + closest() 收敛

### 触发场景
站内导航/浮层外收起。

### 陷阱-正解
**陷阱**：每元素单独绑 click。
**正解**：document click 委托 + closest() 判定。

### 规则
router.js:100-111 / app.js:79 / board/switcher.js:39 示例。

## hover popover 状态机（fixed 定位 + getBoundingClientRect）

### 触发场景
DAG 节点悬浮浮层。

### 陷阱-正解
**陷阱**：浮层被 overflow 裁剪。
**正解**：has-tip[data-tip] / .dag-tip[data-for] 配对；position:fixed 逃逸；mouseenter/leave 切显隐；下方放不下翻上方。

### 规则
board/switcher.js:138-155 完整实现。
