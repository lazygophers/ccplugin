---
title: FTS5 schema 迁移幂等
layer: recall
category: impl
keywords: [fts5,schema,migration,幂等,drop table,reindex]
source: spec-memory-extend
authored-by: skein-spec
created: 1784557917
status: active
related: [deriv-file-exclude]
updated: 1784557917
---

# FTS5 schema 迁移幂等

## 铁律

MUST：`CREATE VIRTUAL TABLE IF NOT EXISTS` 不会修改已存在表的 schema，仅在建表时生效

MUST：加列（ALTER TABLE）操作必须先 `DROP TABLE IF EXISTS` 再 CREATE，确保 schema 更新

MUST：reindex 必须幂等：重复执行应产生相同结果

## 反例表

| 禁 | 改为 |
|---|---|
| 期望 `CREATE IF NOT EXISTS` 自动加列 | 先 DROP 再 CREATE 保证 schema 更新 |
| 迁移脚本非幂等 | 用 IF NOT EXISTS + DROP 组合保证幂等 |
| 加列后索引未重建 | 迁移后触发 reindex 刷新 FTS 索引 |

## 适用
- FTS5 表 schema 演进
- 数据库迁移脚本设计
- 索引重建流程

## 关联
- 衍生文件排除范式（衍生表也需排除）
