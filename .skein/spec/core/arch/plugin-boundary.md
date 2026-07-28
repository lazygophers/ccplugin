---
title: plugin-boundary
layer: core
category: arch
keywords: [skill,外部依赖,硬依赖,优雅降级,mapping,可选引用,arch,场景路由,plan,前置,交互,路由判定,exec]
status: active
---

## skein 零外部 skill 硬依赖

### 铁律 / 契约

- MUST：skein 零外部 skill 硬依赖 — 所有外部 skills 仅通过 mapping 文件可选引用，未装时跳过不报错
- MUST：禁止直接 import 外部 skill（如 `from external_skill import func`），必须映射文件 + try-except 优雅降级
- MUST：mapping 文件为可选参考（如 `references/matt-pocock-mapping.md`），缺失时不阻塞 skein 运行

### 反例表

| 禁 | 改为 |
|---|---|
| 硬依赖外部 skill（直接 import，未装时崩溃） | mapping 文件可选引用 + 优雅降级 |
| 缺少外部 skill 就报错 ImportError | 未装时跳过，不阻塞主流程 |
| 所有功能都强制装齐所有 skills | 核心功能独立运行，外部 skills 为增强 |

### 关联

- [arch] Ponytail 注释模式（性能权衡显式化）
- [planning] 场景路由归 plan 前置

## 场景路由归 plan 前置

### 铁律 / 契约

- MUST：场景路由判定必须在 plan 阶段之前完成（交互在 plan 及之前）
- MUST：禁止在 exec 阶段进行路由判定或向用户询问路由方式
- MUST：plan 完成时必须明确走哪种路由（skein 原生 / 外部 skill / 混合）

### 反例表

| 禁 | 改为 |
|---|---|
| exec 中才问用户选哪种路由方式 | plan 前置完成路由判定 + 交互 |
| 路由判定延迟到 exec 阶段 | plan 开始前完成所有交互 |
| 模糊路由（plan + exec 都不明确） | plan 中明确路由策略再开始 |

### 关联

- [arch] skein 零外部 skill 硬依赖
