---
title: spec 三层记忆架构
layer: recall
category: arch
keywords: [spec,三层架构,core,recall,external,lay,degrade,预算,hook,fts5,bm25]
source: spec-memory-extend
authored-by: skein-spec
created: 1784557943
status: active
related: []
updated: 1784557943
---

# spec 三层记忆架构

## 铁律

MUST：spec 记忆分三层 —— core（常驻注入 hook）+ recall（FTS5 BM25 按需召回）+ external（纯手动 CLI 不入 hook，终点层 degrade 拒）

MUST：LAYERS 元组扩为三层，degrade 单向 core→recall

MUST：core 层硬预算 8000 字符，超则告警降级

## 架构说明

| 层       | 加载方式                      | 适用内容                     | 预算     |
|----------|-------------------------------|------------------------------|----------|
| **core** | SessionStart hook 常驻注入    | 硬约束 / 命令式契约           | 8000 字符 |
| **recall** | 按需语义召回（planning 时）   | 长尾 / 上下文密集经验         | 无限制    |
| **external** | 纯手动 CLI，不入 hook        | 手动维护内容                 | 不注入    |

## 降解流程

- 单向：core → recall（recall 不会回退到 core）
- 触发：core 超预算时，降级最少复用的 core 规则到 recall
- 阻断：external 层永不注入，仅手动访问

## 反例表

| 禁 | 改为 |
|---|---|
| 单一 spec 平面 | 三层分层：core/recall/external |
| core 预算无限 | 软预算 8000，超则告警降级 |
| recall 常驻注入 | 仅按需 BM25 召回 |
| 双向降解 | 单向 core→recall |

## 适用
- spec 库架构设计
- 记忆注入策略
- 预算控制

## 关联
- config 预算复用模式（core_budget）
