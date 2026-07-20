---
title: FTS5 中文 OR 语义
layer: recall
category: impl
keywords: [fts5,中文,分词,unicode61,or,query,match,grep]
source: spec-memory-extend
authored-by: skein-spec
created: 1784557924
status: active
related: [fts5-schema-idempotent]
updated: 1784557924
---

# FTS5 中文 OR 语义

## 铁律

MUST：sqlite3 FTS5 的 unicode61 分词器对中文几乎不分词（整段连续汉字视为一个 token）

MUST：多 token query 必须用双引号包每个 token + OR 连接（任一词命中即召回），逼近 grep OR 语义

MUST：MATCH 对双引号极度敏感，含双引号的 token 须提前降级为 grep

## 反例表

| 禁 | 改为 |
|---|---|
| `MATCH '中文1 OR 中文2'` 期望召回 | 改为 `MATCH '"中文1" OR "中文2"'` 确保分词 |
| 期望 unicode61 自动分中文词 | 它不会 — 用 OR + 双引号强制多 token |
| 含 `"` 的 query 直接送 MATCH | 先检测 `"`，存在则改用 grep |

## 原理

- unicode61 是基于 Unicode 字符的简单分词，对中文连续字符合并成一个 token
- `"token1" OR "token2"` 语法确保每个 token 独立匹配
- MATCH 对引号处理特殊化，含引号词易失效

## 适用
- 中文 FTS 搜索 query 构建
- 多关键词召回场景
- OR 语义实现

## 关联
- FTS5 schema 设计
