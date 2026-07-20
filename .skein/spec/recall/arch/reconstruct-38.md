---
title: task.json 写入口唯一 (_save)，写后自动 _board_task
layer: recall
category: arch
keywords: [write,state,mutation,consistency]
source: reconstruct
authored-by: skein-spec
created: 1784346042
status: active
related: []
updated: 1784346042
---

## 触发场景
修改 task.json。

## 陷阺-正解
**陷阺**：各处直接写 task.json。
**正解**：统一 _save() 入口，写后同步渲染 _board_task()。

## 规则
skein.py:238-243。
