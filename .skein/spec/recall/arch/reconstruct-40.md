---
title: per-task 真值源 + 顶层去规范化镜像
layer: recall
category: arch
keywords: [data,source,task.json,denormalization,sync]
source: reconstruct
authored-by: skein-spec
created: 1784346699
status: active
related: []
updated: 1784346699
---

## 铁律

- MUST：修改状态时只写 `task/<id>/task.json`，不直接写顶层镜像
- MUST：顶层 `.skein/task.json` 每次变更后自动重算（`_sync()` 入口）
- MUST：读顶层镜像用于展示/索引，不作写入决策源

## 反例表

| 禁 | 改为 |
|---|---|
| 修改顶层 task.json 期望子 task 同步 | 仅修改 task/<id>/task.json，_sync() 重算 |
| per-task 与顶层分别维护 | 每次修改一入口，另一衍生 |
| 顶层与 per-task 版本不一致 | 重跑 _sync() |
