---
title: 后端算数据 / 前端呈现（职责分离）
layer: recall
category: arch
keywords: [architecture,separation-of-concerns,data]
source: reconstruct
authored-by: skein-spec
created: 1784346093
status: active
related: []
updated: 1784346093
---

## 触发场景
业务逻辑与数据计算。

## 陷阳-正解
**陷阺**：前端重算 DAG/状态/节点。
**正解**：后端算好经 JSON 下发，前端只做呈现映射（色彩/布局）。

## 规则
Python _board_data() 注 CSS links + 结构化数据；前端 setNodeMaps() 注入映射。
