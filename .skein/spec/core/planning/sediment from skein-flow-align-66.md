---
title: skein-finish 四步序（merge → 销wt → 标记 → 异步spec）
layer: core
category: planning
keywords: [finish,merge,worktree,spec,沉淀,异步,fire-and-forget]
source: sediment from skein-flow-align
authored-by: skein-spec
created: 1784822948
status: active
related: []
updated: 1784822948
---

## 铁律

- MUST：skein-finish 必须按以下四步序执行：
  - ①合并 worktree 到主分支（git merge）
  - ②删除 worktree（git worktree remove）
  - ③标记 task 完成（task.json status=finished）
  - ④异步派 agent 处理记忆/spec（fire-and-forget，不阻塞 finish）
- MUST：步骤顺序不可调，每步失败需明确报告
- MUST：step4（spec sediment）必须异步 fire-and-forget，finish 闭环不等待回传

## 反例表
| 禁 | 改为 |
|---|---|
| 先删 worktree 再 merge | ①merge ②delete ③标记 ④异步spec |
| spec sediment 同步阻塞 finish | spec sediment 异步 fire-and-forget |
| finish 闭环等待所有步骤完成 | 至 step3 即可闭环，step4 异步运行 |

## 触发场景
- task 进入 finish 阶段
- check 阶段全部通过
- 工作树合并与 task 完成

## 关联
- 铁律: exec 阶段无验收勾选
- 铁律: skein-check 两步法
- SPEC 约定: 异步 spec sediment（finish 后自主沉淀记忆）
