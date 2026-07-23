---
title: task 创建规范（task.json + 文件夹初始化）
layer: core
category: planning
keywords: [create,task,文件夹,初始化,prd,design,findings]
source: sediment from skein-flow-align
authored-by: skein-spec
created: 1784822953
status: active
related: []
updated: 1784822953
---

## 铁律

- MUST：建 task = 更新 task.json + 初始化 task 文件夹结构，两步一体
- MUST：task.json 必须含完整的 metadata（id/name/desc/subtasks DAG 等）
- MUST：task 文件夹必须初始化标准结构：task.md + prd.md + design.md + findings.md（如适用）
- MUST：禁用 skein init（初始化操作在 create 阶段完成，勿分离）

## 反例表
| 禁 | 改为 |
|---|---|
| create 后再手动 mkdir task 文件夹 | create 时一步完成文件夹初始化 |
| 先 create task.json，后 skein init 初始化文件夹 | 两步合一在 create 中 |
| task 文件夹缺标准子文件 | create 时生成 prd/design/findings/task 标准文件 |

## 触发场景
- `skein create <task-id>` 命令执行
- task 生命周期启动
- 文件夹结构初始化

## 关联
- 铁律: plan 阶段完成判据门（prd 必须填完）
- 铁律: start 强制 prd 硬门
