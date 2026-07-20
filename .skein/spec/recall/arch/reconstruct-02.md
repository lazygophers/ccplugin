---
title: lib = 共享库层，scripts 单向依赖
layer: recall
category: arch
keywords: [architecture,lib,layer,dependency]
source: reconstruct
authored-by: skein-spec
created: 1784345946
status: active
related: []
updated: 1784345946
---

## 触发场景
提取公用函数/DB 工具时决定放 lib 还是 scripts。

## 陷阱-正解
**陷阱**：库函数散落 scripts/ 各处，或 lib 反向依赖 scripts。
**正解**：通用工具/DB ORM 放 lib，scripts 单向依赖 lib（`from lib...`），lib 不反依赖。

## 规则
依赖图：scripts → lib，不反向。

## 关联
arch/monorepo-layer-isolation, arch/circular-dependency-prevention
