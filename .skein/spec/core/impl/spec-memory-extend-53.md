---
title: 衍生文件排除范式
layer: core
category: impl
keywords: [fts,衍生文件,backlinks,glob排除,测试断言]
source: spec-memory-extend
authored-by: skein-spec
created: 1784557912
status: active
related: [fts5-schema-idempotent,chinese-or-semantics]
updated: 1784557912
---

# 衍生文件排除范式

## 铁律

MUST：新增衍生文件（如 `backlinks.md` 或 `.recall.db`）必须在 `_rule_files` glob 中排除

MUST：排除的衍生文件也必须在测试断言中排除，否则 FTS 索引/反链扫描会把衍生文件当作规则处理

MUST：防止递归自引用：衍生文件不应被索引为规则本身

## 反例表

| 禁 | 改为 |
|---|---|
| `_rule_files = ["*.md"]` 包含衍生文件 | `_rule_files = ["*.md", "!backlinks.md"]` 显式排除 |
| 测试断言包含衍生文件 | 测试断言也加 `!= "backlinks.md"` 等排除逻辑 |
| FTS 把衍生文件当规则 | 在 glob pattern 中排除衍生文件 |

## 关联
- FTS5 索引设计
- 测试断言完整性
