---
name: orchestration
description: 多任务编排规范 - 团队组建、任务分配、通信协调、并行调度和异常处理
user-invocable: true
context: fork
model: sonnet
memory: project
---

# 多任务编排规范

## 团队生命周期

```
组建团队 → 创建任务 → 建立依赖 → 生成成员 → 分配任务 → 调度循环 → 关闭团队
```

### 组建团队
使用 `TeamCreate` 创建专属团队，团队名格式 `task-<plan-id>`。

### 创建任务与依赖
使用 `TaskCreate` 为每个子任务创建条目。使用 `TaskUpdate` 的 `addBlockedBy` 建立依赖关系，被阻塞的任务在前置完成前无法认领。

### 生成团队成员
使用 `Agent` 并指定 `team_name` 和 `name` 生成成员加入团队。根据任务类型选择 `subagent_type`：
- 需要修改代码的任务 → `general-purpose`
- 只需读取分析的任务 → `Explore`
- 只需规划不需实现的任务 → `Plan`

成员命名：executor-1、executor-2、reviewer-1、debugger-1。

### 分配任务
使用 `TaskUpdate` 设置 `owner` 和 `status=in_progress` 分配任务。使用 `SendMessage` 通知成员开始执行。

分配前检查：
- 任务 pending 且无 blockedBy
- 与当前并行任务的 target_files 无交集
- 当前并行成员数未超过 2

### 调度循环

```
while 存在未完成任务:
    等待成员消息（自动送达，无需轮询）
    收到完成通知 → 用 TaskList 找下一个可执行任务 → SendMessage 分配
    收到问题上报 → 评估后指导/重试/升级/向用户提问
    所有任务完成 → 触发 Oracle 验证 → 关闭团队
```

### 关闭团队
使用 `SendMessage` 的 shutdown_request 逐个关闭成员。全部关闭后使用 `TeamDelete` 清理。

## 通信规范

### 何时用点对点消息
- 给成员分配新任务时
- 指导成员修复问题时
- 回应成员的问题上报时
- 通知成员计划变更时

### 何时用全员广播
仅用于紧急阻塞性问题：发现严重依赖冲突、需全员暂停、T1 输出结构变更影响所有后续任务。

### 何时向用户提问
使用 `AskUserQuestion` ：
- 成员上报的问题无法自行决策时
- 三次失败升级到用户层时
- 任务目标需要澄清时
- 存在多种实现方案需用户选择时

提问必须包含：问题背景、已尝试的方案、可选方向和推荐建议。

### 成员 idle 状态
成员完成任务后自动 idle，这是正常行为。idle 的成员可以被 SendMessage 唤醒并分配新任务。

## 编排模式

### 顺序执行
任务逐个执行，通过 addBlockedBy 串联。适用于强依赖链。

### 并行分组
无依赖的任务由不同成员并行执行（最多 2 个）。分配前检查 target_files 无交集。

### 流水线
执行者和审查者交替工作：执行一组 → 审查 → 执行下一组 → 审查。

### 迭代（Loop）
执行者和审查者协作迭代：executor 执行 → reviewer 验证 → 失败则 executor 调整重试。

## 异常处理

### 失败升级链
- 第 1 次：使用 `SendMessage` 指导 executor 调整后重试
- 第 2 次：生成 debugger 成员介入诊断根因，使用 `SendMessage` 发送失败上下文
- 第 3 次：reviewer 审查任务定义是否合理，必要时让 planner 重新规划
- 仍然失败：使用 `AskUserQuestion` 向用户报告问题，请求指导

通过 metadata.retry_count 追踪重试次数。

### 级联阻塞
任务失败后，依赖它的后续任务因 blockedBy 自动无法认领。修复并标记 completed 后自动解除。

### 成员异常
- 长时间无响应 → 使用 `SendMessage` 询问状态
- 进程崩溃 → 使用 `TaskStop` 终止，生成新成员接替

## 执行过程检查清单

### 组建团队阶段
- [ ] 使用 `TeamCreate` 创建专属团队
- [ ] 团队名格式符合 `task-<plan-id>`
- [ ] 团队目标明确

### 创建任务与依赖阶段
- [ ] 使用 `TaskCreate` 为每个子任务创建条目
- [ ] 使用 `TaskUpdate` 的 `addBlockedBy` 建立依赖关系
- [ ] 依赖关系准确（被阻塞的任务在前置完成前无法认领）
- [ ] 任务状态初始化为 `pending`

### 生成团队成员阶段
- [ ] 使用 `Agent` 并指定 `team_name` 和 `name`
- [ ] 根据任务类型选择合适的 `subagent_type`
- [ ] 成员命名规范（executor-1、reviewer-1 等）
- [ ] 成员数量合理（不超过并行需求）

### 分配任务阶段
- [ ] 任务状态为 `pending` 且无 `blockedBy`
- [ ] 与当前并行任务的 `target_files` 无交集
- [ ] 当前并行成员数未超过 2
- [ ] 使用 `TaskUpdate` 设置 `owner` 和 `status=in_progress`
- [ ] 使用 `SendMessage` 通知成员开始执行

### 调度循环阶段
- [ ] 等待成员消息（自动送达，无需轮询）
- [ ] 收到完成通知 → 使用 `TaskList` 找下一个可执行任务
- [ ] 收到问题上报 → 评估后指导/重试/升级/向用户提问
- [ ] 所有任务完成 → 触发 Oracle 验证

### 通信协调检查
- [ ] 点对点消息用于分配任务、指导修复、回应问题
- [ ] 全员广播仅用于紧急阻塞性问题
- [ ] 向用户提问包含问题背景、已尝试方案、可选方向和推荐建议
- [ ] 成员 idle 状态被正常处理（可被 SendMessage 唤醒）

### 异常处理检查
- [ ] 通过 `metadata.retry_count` 追踪重试次数
- [ ] 第 1 次失败 → SendMessage 指导 executor 调整重试
- [ ] 第 2 次失败 → 生成 debugger 成员介入诊断
- [ ] 第 3 次失败 → reviewer 审查任务定义，必要时 planner 重新规划
- [ ] 仍然失败 → AskUserQuestion 向用户报告问题
- [ ] 任务失败后，依赖它的后续任务自动被阻塞

## 完成后检查清单

### 关闭团队检查
- [ ] 使用 `SendMessage` 的 shutdown_request 逐个关闭成员
- [ ] 所有成员已关闭
- [ ] 使用 `TeamDelete` 清理团队
- [ ] 团队资源已释放

### 任务完成检查
- [ ] 所有任务状态为 `completed`
- [ ] Oracle 验证已通过
- [ ] 执行报告已输出
- [ ] TaskList 已清理（已完成任务已归档）

### 状态记录检查
- [ ] 所有任务 metadata 包含完整执行记录
- [ ] 失败任务的失败原因已记录
- [ ] 重试次数已正确追踪
- [ ] 执行时长和完成时间戳已记录
