---
title: maintain archive_reasons 覆盖 guard
layer: recall
category: impl
keywords: [maintain,archive_reasons,guard,dict覆盖,多finding,orphan]
source: spec-memory-extend
authored-by: skein-spec
created: 1784557930
status: active
related: []
updated: 1784557930
---

# maintain archive_reasons 覆盖 guard

## 铁律

MUST：maintain --apply 收集 archive_reasons dict[Path, tuple] 时，后处理判据（如 orphan）必须先查 `if f not in archive_reasons:` guard

MUST：否则同一文件可能触发多个 finding（如同时 stale + orphan），后面的覆盖前面的 reason，导致输出标签错误

## 反例表

| 禁 | 改为 |
|---|---|
| `archive_reasons[f] = ("stale", ...)` 后直接再 `archive_reasons[f] = ("orphan", ...)` | 先检查 `if f not in archive_reasons:` 再覆盖 |
| 期望多 finding 累积 | 只保留第一个 finding，或改用 list 存多 reasons |
| orphan 判据直接覆盖 | 先检查文件是否已在 reasons 中 |

## 原理

- dict 赋值会覆盖已有值
- 同一文件可能命中多个判据（如 stale 且 orphan）
- 不加 guard 会导致只保留最后一个 finding 的 reason

## 适用
- maintain --apply 的 finding 收集
- dict 覆盖风险场景
- 多标签累积逻辑

## 关联
- spec 维护流程
