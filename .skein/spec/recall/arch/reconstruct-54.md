---
title: DB 多后端适配器模式（BaseAdapter + per-db 子类）
layer: recall
category: arch
keywords: [design-pattern,adapter,database,abstraction]
source: reconstruct
authored-by: skein-spec
created: 1784346093
status: active
related: []
updated: 1784346093
---

## 触发场景
支持多数据库（MySQL/PostgreSQL/SQLite）。

## 陷阳-正解
**陷阺**：SQL 硬编码或特定数据库逻辑散落。
**正解**：统一 DatabaseAdapter → BaseAdapter，未实现方法 raise NotImplementedError；各 db 子类实现。

## 规则
lib/db/adapters/ 结构。
