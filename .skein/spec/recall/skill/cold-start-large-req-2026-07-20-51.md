---
title: supertask/task 父子层结构契约
layer: recall
category: skill
keywords: [supertask,parent,child,finish,深度限2层,create守卫]
source: cold-start-large-req-2026-07-20
authored-by: skein-spec
created: 1784541818
status: active
related: []
updated: 1784541818
---

# supertask/task 父子层结构契约

## 铁律
SKEIN task 深度限 2 层：`supertask → task → subtask`。禁止三层嵌套。

## 结构守卫（create() 单点）
- **parent 链合法性**：创建 task 时，若 `parent` 非空，必须检查 `parent.parent == None`
- 违反则拒绝创建：三层嵌套（supertask→task→subtask→更深）禁止
- 守卫位置：仅在 `create()` 函数单点检查，所有创建路径必经此函数

## finish 聚合规则
| 任务类型 | finish 前提 |
|---------|------------|
| **supertask** | 所有 child 须全 `done` 状态；否则 finish 拒绝 |
| **task** | 不查 parent 状态，独立 finish |
| **subtask** | 不查 parent 状态，独立 finish |

## 真值源单一性
- **仅靠 `_all()` 过滤**：查询 child 时，用 `lambda t: t.parent == tid` 过滤
- **禁维护 child_ids 反向数组**：不在 parent 对象存储 child 列表，防止数据不一致
- 单向依赖：child 持 parent 引用，parent 不存 child 列表

## 默认行为
- **不建 supertask**：仅大需求（涉及多模块/需分阶段）创建 supertask
- 小需求直接创建 task，不强制 supertask 层

## 适用场景
- 后续所有 SKEIN task 创建/finish 操作必遵此契约
- supertask 用于编排复杂工作流（多阶段、跨模块）

## 关联
- 参考 `task.json schema 加字段必查 doctor 字段禁令清单` 中的 parent 解禁
