---
title: 场景路由归 plan 前置
layer: core
category: arch
keywords: [场景路由,plan,前置,交互,路由判定,exec,arch]
source: ask-matt-integrate
authored-by: skein-spec
created: 1784651636
status: active
related: []
updated: 1784651636
---

## 铁律 / 契约

- MUST：场景路由判定必须在 plan 阶段之前完成（交互在 plan 及之前）
- MUST：禁止在 exec 阶段进行路由判定或向用户询问路由方式
- MUST：plan 完成时必须明确走哪种路由（skein 原生 / 外部 skill / 混合）

## 反例表

| 禁 | 改为 |
|---|---|
| exec 中才问用户选哪种路由方式 | plan 前置完成路由判定 + 交互 |
| 路由判定延迟到 exec 阶段 | plan 开始前完成所有交互 |
| 模糊路由（plan + exec 都不明确） | plan 中明确路由策略再开始 |

## 关联

- [arch] skein 零外部 skill 硬依赖
