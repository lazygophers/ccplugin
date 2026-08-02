---
title: task-flow
layer: recall
category: planning
keywords: [task,状态机,待处理,就绪,进行中,检查中,done,check,状态转移,占槽,多task协调]
status: active
---

## task 状态流转规则（单 task 全 done → check）

### 铁律

- MUST：task 状态机：待处理(规划中) ⇄ 调研中(research) →[confirm, 吸收原 start 全部职责]→ 进行中 →[check]→ 检查中 →[finishing]→ 收尾中 →[finish]→ 已完成；「就绪」中间态已删
- MUST：**work 池 (`pools.work`) 计数全局 phase∈{exec,research} 且 status=运行中的 subtask；gate 池 (`pools.gate`) 计数 status∈{检查中,收尾中} 的 task**；`confirm` 本身不占任何池，task 级「同时几个 task 进行中」上限已取消
- MUST：单个 task 中所有 subtask 状态为 done → `skein check` 将该 task 从进行中→检查中（check 是独立阶段/独立状态，独立验收）
- MUST：多 task 场景下，全部 task 都完成才标记 exec 暂停（等待用户启动下一 task）
- MUST：task 进 check 不需等待同批其他 task 完成（每个 task 独立流转）
- MUST：状态转移必须在脚本中明确处理（非隐式逻辑）；有 worktree 的在途态 = {进行中, 检查中, 收尾中}（finish/del 销 worktree 按此判）

### 反例表
| 禁 | 改为 |
|---|---|
| 等所有 task 完成才进 check | 单 task 全 subtask done 立即 `skein check` 进检查中 |
| task 之间相互阻塞等待 | 各 task 独立流转，无依赖则并行进 check |
| 检查中/收尾中占 pools.work 槽 | 检查中/收尾中占 gate 槽；work 槽仅进行中/调研中的 subtask 占 |
| 检查中/收尾中 task 不销 worktree(finish/del) | 在途态={进行中,检查中,收尾中} 均有 worktree，均须销 |
| exec 无明确状态转移逻辑 | 脚本明确处理 done→check 转移 |

### 触发场景
- task 中最后一个 subtask 完成时
- 多 task workflow 中的状态协调
- exec 到 check 的自动流转

### 关联
- 铁律: exec 阶段无验收勾选
- 铁律: skein-check 两步法
- 铁律: skein-finish 四步序
