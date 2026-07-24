---
title: task 状态流转规则（单 task 全 done → check）
layer: core
category: planning
keywords: [task,状态机,待处理,就绪,进行中,检查中,done,check,状态转移,占槽,多task协调]
source: sediment from skein-flow-align
authored-by: skein-spec
created: 1784822937
status: active
related: []
updated: 1784910100
---

## 铁律

- MUST：task 五态机：待处理(规划中) →[confirm]→ 就绪(待启动) →[start]→ 进行中 →[check]→ 检查中 →[finish]→ 已完成
- MUST：**占 max_active 槽的仅「进行中」**；待处理/就绪/检查中均**不占槽**（就绪不占→可提前备料；检查中不占→check 期释放槽给下个 task start）
- MUST：单个 task 中所有 subtask 状态为 done → `skein check` 将该 task 从进行中→检查中（check 是独立阶段/独立状态，独立验收）
- MUST：多 task 场景下，全部 task 都完成才标记 exec 暂停（等待用户启动下一 task）
- MUST：task 进 check 不需等待同批其他 task 完成（每个 task 独立流转）
- MUST：状态转移必须在 skein.py 中明确处理（非隐式逻辑）；有 worktree 的在途态 = {进行中, 检查中}（finish/del 销 worktree 按此判）

## 反例表
| 禁 | 改为 |
|---|---|
| 等所有 task 完成才进 check | 单 task 全 subtask done 立即 `skein check` 进检查中 |
| task 之间相互阻塞等待 | 各 task 独立流转，无依赖则并行进 check |
| 检查中仍占 max_active 槽 | 仅进行中占槽；检查中释放槽给下个 task |
| 检查中 task 不销 worktree(finish/del) | 在途态={进行中,检查中} 均有 worktree，均须销 |
| exec 无明确状态转移逻辑 | skein.py 明确处理 done→check 转移 |

## 触发场景
- task 中最后一个 subtask 完成时
- 多 task workflow 中的状态协调
- exec 到 check 的自动流转

## 关联
- 铁律: exec 阶段无验收勾选
- 铁律: skein-check 两步法
- 铁律: skein-finish 四步序
