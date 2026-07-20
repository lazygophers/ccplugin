---
title: document click 委托 + closest() 收敛
layer: recall
category: frontend
keywords: [event,delegation,dom,pattern]
source: reconstruct
authored-by: skein-spec
created: 1784346092
status: active
related: []
updated: 1784346092
---

## 触发场景
站内导航/浮层外收起。

## 陷阳-正解
**陷阺**：每元素单独绑 click。
**正解**：document click 委托 + closest() 判定。

## 规则
router.js:100-111 / app.js:79 / board/switcher.js:39 示例。
