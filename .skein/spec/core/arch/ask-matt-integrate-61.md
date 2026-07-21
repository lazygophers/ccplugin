---
title: skein 零外部 skill 硬依赖
layer: core
category: arch
keywords: [skill,外部依赖,硬依赖,优雅降级,mapping,可选引用,arch]
source: ask-matt-integrate
authored-by: skein-spec
created: 1784651635
status: active
related: []
updated: 1784651635
---

## 铁律 / 契约

- MUST：skein 零外部 skill 硬依赖 — 所有外部 skills 仅通过 mapping 文件可选引用，未装时跳过不报错
- MUST：禁止直接 import 外部 skill（如 `from external_skill import func`），必须映射文件 + try-except 优雅降级
- MUST：mapping 文件为可选参考（如 `references/matt-pocock-mapping.md`），缺失时不阻塞 skein 运行

## 反例表

| 禁 | 改为 |
|---|---|
| 硬依赖外部 skill（直接 import，未装时崩溃） | mapping 文件可选引用 + 优雅降级 |
| 缺少外部 skill 就报错 ImportError | 未装时跳过，不阻塞主流程 |
| 所有功能都强制装齐所有 skills | 核心功能独立运行，外部 skills 为增强 |

## 关联

- [arch] Ponytail 注释模式（性能权衡显式化）
- [planning] 场景路由归 plan 前置
