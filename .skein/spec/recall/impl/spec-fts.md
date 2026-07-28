---
title: spec-fts
layer: recall
category: impl
keywords: [fts5,schema,migration,幂等,drop table,reindex,中文,分词,unicode61,or,query,match,grep,maintain,archive_reasons,guard,dict覆盖,多finding,orphan,config,预算,budget,core_budget,懒读取,fallback,热修改]
status: active
---

## FTS5 schema 迁移幂等

### FTS5 schema 迁移幂等

### 铁律

MUST：`CREATE VIRTUAL TABLE IF NOT EXISTS` 不会修改已存在表的 schema，仅在建表时生效

MUST：加列（ALTER TABLE）操作必须先 `DROP TABLE IF EXISTS` 再 CREATE，确保 schema 更新

MUST：reindex 必须幂等：重复执行应产生相同结果

### 反例表

| 禁 | 改为 |
|---|---|
| 期望 `CREATE IF NOT EXISTS` 自动加列 | 先 DROP 再 CREATE 保证 schema 更新 |
| 迁移脚本非幂等 | 用 IF NOT EXISTS + DROP 组合保证幂等 |
| 加列后索引未重建 | 迁移后触发 reindex 刷新 FTS 索引 |

### 适用
- FTS5 表 schema 演进
- 数据库迁移脚本设计
- 索引重建流程

### 关联
- 衍生文件排除范式（衍生表也需排除）

## FTS5 中文 OR 语义

### FTS5 中文 OR 语义

### 铁律

MUST：sqlite3 FTS5 的 unicode61 分词器对中文几乎不分词（整段连续汉字视为一个 token）

MUST：多 token query 必须用双引号包每个 token + OR 连接（任一词命中即召回），逼近 grep OR 语义

MUST：MATCH 对双引号极度敏感，含双引号的 token 须提前降级为 grep

### 反例表

| 禁 | 改为 |
|---|---|
| `MATCH '中文1 OR 中文2'` 期望召回 | 改为 `MATCH '"中文1" OR "中文2"'` 确保分词 |
| 期望 unicode61 自动分中文词 | 它不会 — 用 OR + 双引号强制多 token |
| 含 `"` 的 query 直接送 MATCH | 先检测 `"`，存在则改用 grep |

### 原理

- unicode61 是基于 Unicode 字符的简单分词，对中文连续字符合并成一个 token
- `"token1" OR "token2"` 语法确保每个 token 独立匹配
- MATCH 对引号处理特殊化，含引号词易失效

### 适用
- 中文 FTS 搜索 query 构建
- 多关键词召回场景
- OR 语义实现

### 关联
- FTS5 schema 设计

## maintain archive_reasons 覆盖 guard

### maintain archive_reasons 覆盖 guard

### 铁律

MUST：maintain --apply 收集 archive_reasons dict[Path, tuple] 时，后处理判据（如 orphan）必须先查 `if f not in archive_reasons:` guard

MUST：否则同一文件可能触发多个 finding（如同时 stale + orphan），后面的覆盖前面的 reason，导致输出标签错误

### 反例表

| 禁 | 改为 |
|---|---|
| `archive_reasons[f] = ("stale", ...)` 后直接再 `archive_reasons[f] = ("orphan", ...)` | 先检查 `if f not in archive_reasons:` 再覆盖 |
| 期望多 finding 累积 | 只保留第一个 finding，或改用 list 存多 reasons |
| orphan 判据直接覆盖 | 先检查文件是否已在 reasons 中 |

### 原理

- dict 赋值会覆盖已有值
- 同一文件可能命中多个判据（如 stale 且 orphan）
- 不加 guard 会导致只保留最后一个 finding 的 reason

### 适用
- maintain --apply 的 finding 收集
- dict 覆盖风险场景
- 多标签累积逻辑

### 关联
- spec 维护流程

## config 预算复用模式

### config 预算复用模式

### 铁律

MUST：预算类常量（如 CORE_BUDGET）应迁移到 config.yaml 使用户可配置（默认 1000）

MUST：实现 `core_budget() -> int` 模式：懒读取（每次调用时读 config 支持热修改）+ 局部 `from skein import _yaml_load` 避免循环依赖 + 缺失/非数字时 fallback 默认值

MUST：后续 spec 阈值类常量走 config 而非硬编码

### 反例表

| 禁 | 改为 |
|---|---|
| `CORE_BUDGET = 1000` 硬编码常量 | 迁移到 config.yaml + core_budget() 函数 |
| 启动时一次性读 config 固化 | 每次调用时读，支持热修改 |
| config 缺失时崩溃 | fallback 到默认值 |
| 直接 `import skein.spec` 导致循环依赖 | 局部 import `_yaml_load` |

### 模式

```python
def core_budget() -> int:
    """懒读取 config 中 core_budget，支持热修改 + fallback"""
    from skein import _yaml_load
    cfg = _yaml_load()
    val = cfg.get("core_budget", 1000)
    try:
        return int(val)
    except (ValueError, TypeError):
        return 1000
```

### 适用
- 所有预算/阈值类常量
- 需要用户可配置的数值
- 热修改需求场景

### 关联
- spec 三层架构（core 预算控制）
