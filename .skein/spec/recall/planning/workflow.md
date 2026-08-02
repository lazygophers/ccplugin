---
title: workflow
layer: recall
category: planning
keywords: [workflow,连线,阶段,确认,confirm,就绪,ready,start,自动,状态转移,exec,验收,checkpoint,职责划分,check阶段,check,场景自适应,编程任务,文案任务,finish,merge,worktree,spec,沉淀,异步,fire-and-forget]
status: active
---

## skein 工作流连线（create → plan → confirm(吸收 start, 直进进行中) → exec → check → finishing → finish）

### 铁律

- MUST：skein 工作流必须明确连线：create(待处理) → plan → `skein confirm --approved`(用户确认门, **吸收原 start 全部职责**, 一步占 worktree→进行中) → exec → `skein check`(→检查中) → `skein finishing`(占 gate 槽→收尾中) → finish(→已完成)
- MUST：plan 阶段完成后需**明确的用户确认门 `skein confirm <id>`**（验 prd + ≥1 subtask + 预计工时）将 task 从**待处理→进行中**；确认门与开工是同一次调用，无独立中间状态
- MUST：**「就绪」中间态已删** —— 人审通过的下一秒就该开工，没人真的会停在那儿 (design.md §1)；`confirm` 本身**不占任何池**，真正的资源约束落在 work 池 (subtask 运行中) 与 gate 池 (检查中/收尾中)
- MUST：`skein confirm` 校验 deps + doctor 体检（prd/subtask/工时已在同一次调用内校验），通过后 task→进行中并进入 exec（无需额外用户操作、无需额外命令）
- MUST：各阶段职责明确，阶段间状态转移在脚本中硬编码（非隐式推断）

### 反例表
| 禁 | 改为 |
|---|---|
| plan 直接自动 confirm | plan 完成后须先走人审门 `skein confirm --approved`（用户批准）再开工 |
| 待处理 task 跳过用户批准直接开工 | 必须先 `skein confirm --approved`，无批准即拒 |
| 期待「就绪」独立命令/独立状态 | confirm 已吸收原 start 全部职责，无就绪中间态 |
| 就绪/检查中 占 pools.work 槽 | 仅进行中占 work 槽；检查中/收尾中占 gate 槽 |
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

- MUST：`skein finish` 只接受**收尾中**态入参（check 全绿后须先 `skein finishing` 占 gate 槽把 task 转收尾中，finish 才能跑），检查中态直接 finish 会被拒
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
