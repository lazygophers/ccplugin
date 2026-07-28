---
title: workflow
layer: recall
category: planning
keywords: [workflow,连线,阶段,确认,confirm,就绪,ready,start,自动,状态转移,exec,验收,checkpoint,职责划分,check阶段,check,场景自适应,编程任务,文案任务,finish,merge,worktree,spec,沉淀,异步,fire-and-forget]
status: active
---

## skein 工作流连线（create → plan → confirm(就绪) → start → exec → check → finish）

### 铁律

- MUST：skein 工作流必须明确连线：create(待处理) → plan → `skein confirm`(用户确认门→就绪) → `skein start`(占槽→进行中) → exec → `skein check`(→检查中) → finish(→已完成)
- MUST：plan 阶段完成后需**明确的用户确认门 `skein confirm <id>`**（验 prd + ≥1 subtask）将 task 从**待处理→就绪**；确认是独立阶段/独立状态，不隐含在 start 内
- MUST：**就绪**是独立状态（规划完成待启动，**不占 max_active 槽**）；只有**就绪** task 可 `skein start`，待处理(规划中) 必须先 confirm 过门
- MUST：`skein start` 仅验 deps + 空槽（prd/subtask 已在 confirm 校验），start 后 task→进行中并进入 exec（无需额外用户操作）
- MUST：各阶段职责明确，阶段间状态转移在脚本中硬编码（非隐式推断）

### 反例表
| 禁 | 改为 |
|---|---|
| plan 直接自动 start | plan 完成后须先 `skein confirm` 过用户门(→就绪) 再 start |
| 待处理 task 直接 start | 仅就绪 task 可 start；待处理须先 confirm |
| 确认门隐含在 start 内 | confirm 是独立命令/独立状态(待处理→就绪)，与 start 分离 |
| 就绪/检查中 占 max_active 槽 | 仅进行中占槽；就绪/检查中不占 |
| 阶段转移隐式进行 | 阶段转移在代码中明确处理 |

### 触发场景
- task 工作流设计
- skein flow 图与执行逻辑对齐
- UI/CLI 交互设计

### 关联
- 铁律: plan 阶段完成判据门
- 铁律: task 状态流转规则
- 实现细节: skein-flow.mmd 流程图

## exec 阶段无验收勾选（验收全归 check）

### 铁律

- MUST：exec 阶段任务调度循环禁勾验收(checkpoint)，仅 done/fail 两态转移
- MUST：所有验收(checkpoint)职责转移到 check 阶段（skein-check 承载）
- MUST：exec skill 循环仅负责执行 subtask，不触发验收逻辑

### 反例表
| 禁 | 改为 |
|---|---|
| exec 调度循环内勾 subtask checkpoint | 删除 exec 中的勾验收逻辑 |
| 验收判断分散在 exec/check 两阶段 | 验收全部在 check 阶段集中 |
| exec 完成后直接标记验收 | exec 仅 done/fail，验收由 check 处理 |

### 触发场景
- exec skill 调度 subtask 时
- skein-executor agent 改进
- task 执行流程对齐

### 关联
- 铁律: skein-check 两步法（checkpoint + 场景自适应）
- 铁律: task 状态流转规则（单 task 全 done → check）

## skein-check 两步法（checkpoint + 场景自适应）

### 铁律

- MUST：skein-check 阶段分两步法：①checkpoint 核对 ②场景自适应内置 check
- MUST：step1（checkpoint 核对）= 逐条核对 task+subtask 的 `--check 项`，标记完成
- MUST：step2（场景自适应 check）= 根据 task 类型执行内置校验：
  - 编程 task → build/test/lint/type/架构一致性
  - 小说/文案 task → 逻辑/设定/伏笔一致性
  - 其他 task → domain-specific checks
- MUST：两步都通过才能进 finish 阶段

### 反例表
| 禁 | 改为 |
|---|---|
| check 阶段只核对 checkpoint，不做质量检查 | 加 step2 场景自适应 check |
| 所有 task 用同一套 check 标准 | 按类型自适应检查规则 |
| 质量检查分散在 exec 阶段 | 集中在 check 阶段两步法处理 |

### 触发场景
- task 进入 check 阶段
- skein-check skill 改进
- 验收标准明确化

### 关联
- 铁律: exec 阶段无验收勾选
- 铁律: task 状态流转规则
- 铁律: skein-finish 四步序

## skein-finish 四步序（merge → 销wt → 标记 → 异步spec）

### 铁律

- MUST：skein-finish 必须按以下四步序执行：
  - ①合并 worktree 到主分支（git merge）
  - ②删除 worktree（git worktree remove）
  - ③标记 task 完成（task.json status=finished）
  - ④异步派 agent 处理记忆/spec（fire-and-forget，不阻塞 finish）
- MUST：步骤顺序不可调，每步失败需明确报告
- MUST：step4（spec sediment）必须异步 fire-and-forget，finish 闭环不等待回传

### 反例表
| 禁 | 改为 |
|---|---|
| 先删 worktree 再 merge | ①merge ②delete ③标记 ④异步spec |
| spec sediment 同步阻塞 finish | spec sediment 异步 fire-and-forget |
| finish 闭环等待所有步骤完成 | 至 step3 即可闭环，step4 异步运行 |

### 触发场景
- task 进入 finish 阶段
- check 阶段全部通过
- 工作树合并与 task 完成

### 关联
- 铁律: exec 阶段无验收勾选
- 铁律: skein-check 两步法
- SPEC 约定: 异步 spec sediment（finish 后自主沉淀记忆）
