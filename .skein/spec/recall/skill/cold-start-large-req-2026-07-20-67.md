---
title: task.json schema 加字段必查 doctor 字段禁令清单
layer: recall
category: skill
keywords: [task.json,doctor,字段白名单,parent,向后兼容,.get()兜底]
source: cold-start-large-req-2026-07-20
authored-by: skein-spec
created: 1784541832
status: active
related: []
updated: 1784541832
---

# task.json schema 加字段必查 doctor 字段禁令清单

## 触发场景
task.json 加新字段时，需先确认字段是否在 `doctor` 禁令清单中；若在禁令中，需先解禁再添加。

## doctor 字段白名单机制
- **doctor 是字段白名单的反面**：白名单外的字段默认禁止，需显式解禁
- 加新字段前，检查是否在 `doctor` 禁令清单；若在，必须先从禁令移出

## 原 parent 禁令冲突
- 原 `parent` 字段被 doctor 禁止
- 与 supertask 需求冲突（需 parent 引用）
- **已解禁**（st1）：parent 可用，但需守卫合法性（`parent.parent == None`）

## 向后兼容策略
- **读侧兜底**：读取 task.json 时，用 `.get()` 默认值兜底
- 不激进迁移旧文件：存量 task.json 缺新字段时，读侧默认值补齐，不强制重写
- 新建 task 时写新字段，旧任务保持兼容

## 适用场景
- 每次加新 task.json 字段前，必查 doctor 禁令
- 读代码用 `.get(field, default)` 兜底，防 KeyError

## 关联
- 参考 `supertask/task 父子层结构契约` 中的 parent 守卫
