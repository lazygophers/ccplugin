---
description: Agentic Loop 持续执行 - 进入 gather-act-verify 循环模式，持续迭代直到任务目标达成或触发终止条件
argument-hint: [任务目标描述]
model: sonnet
memory: project
preferred_subagent: orchestrator
---

# Agentic Loop 持续执行

**推荐使用 `orchestrator` Agent 作为团队领导来执行 Loop 模式**，orchestrator 会组建多 Agent 团队并协调执行。

你将进入 Agentic Loop 模式，持续迭代执行直到目标达成。

## 循环结构

```
iteration = 0

while True:
    iteration += 1

    # Phase 1: Gather - 收集当前上下文
    gather_context()

    # Phase 2: Act - 执行操作
    take_action()

    # Phase 3: Verify - 验证结果
    result = verify_result()

    if result.passed:
        report_success()
        break

    if result.no_progress:
        report_stalled()
        ask_user_for_guidance()
        break

    # Phase 4: Adjust - 调整策略
    adjust_strategy(result.feedback)
```

## 执行规范

### Phase 1: Gather（收集）

- 读取当前代码状态、测试结果、错误日志
- 收集可用的 skills 和 agents，评估本次迭代需要哪些能力
- 理解上一次迭代的变更和反馈
- 通过 `TaskList` / `TaskGet` 确认当前任务状态
- 确定本次迭代的具体目标
- 选择合适的 agents 执行本次迭代（可并行分配独立子目标）

### Phase 2: Act（执行）

- 基于收集的信息做出具体变更
- 将独立的子目标分配给不同 agents 并行执行，如果超过最大并行数，则在队列中等待
- 并行任务不得修改同一文件或同一包
- 每个 agent 每次只做一个逻辑变更，保持原子性
- 变更后立即保存

### Phase 3: Verify（验证）

- 运行测试或检查命令验证变更效果
- 对比预期输出和实际输出
- 判断是否达成目标

### Phase 4: Adjust（调整）

- 分析验证失败的原因
- 调整下一次迭代的策略
- 如果连续 2 次无进展，终止循环并报告

## 终止条件

1. **目标达成**：所有验证条件通过
2. **无进展**：连续 2 次迭代错误相同
3. **用户终止**：用户主动中断

## 输出格式

每次迭代输出：

```
--- 迭代 N ---
[Gather] 当前状态摘要
[Act] 本次变更描述
[Verify] 验证结果：通过/失败 - 原因
[Adjust] 下次调整策略（如需继续）
```

最终输出：

```
--- Loop 完成 ---
状态：成功/失败/超时
总迭代次数：N
变更摘要：[所有变更的简要列表]
```

## 与其他命令协作

Loop 在迭代过程中可以调用其他 task 命令来组织具体行为：

| 命令      | 在 Loop 中的用途           |
| --------- | -------------------------- |
| `/plan`   | 规划分解                   |
| `/exec`   | 执行已规划好的子任务       |
| `/review` | 每轮迭代后审查变更质量     |
| `/add`    | 用户中途补充说明或纠正方向 |

**典型 Loop + Commands 协作流程**：

```
Loop 迭代 1:
  [Gather] 收集状态 → 发现需要规划
  [Act]    调用 /plan 分解任务
  [Verify] 确认计划合理

Loop 迭代 2:
  [Gather] 读取任务状态
  [Act]    调用 /exec 执行第一组子任务
  [Verify] 调用 /review 审查结果 → 部分失败

Loop 迭代 3:
  [Gather] 读取失败原因
  [Act]    修复失败的子任务
  [Verify] 调用 /review 审查 → 全部通过
```

## 适用场景

- 修复测试失败（迭代修复直到所有测试通过）
- 性能优化（迭代优化直到达标）
- 代码重构（迭代重构直到 lint 通过）
- 功能实现（迭代实现直到验收通过）

## 注意事项

- 每次迭代必须有可观测的进展
- 不要在一次迭代中做过多变更
- 保持每次迭代的上下文连贯
- 遇到需要用户决策的问题时立即中断循环
- 每次迭代后通过 `TaskUpdate` 更新任务状态和 metadata
