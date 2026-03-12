---
description: Agentic Loop 持续执行 - 进入 gather-act-verify 循环模式，持续迭代直到任务目标达成或触发终止条件
argument-hint: [任务目标描述]
model: sonnet
memory: project
---

# Agentic Loop 持续执行

你将进入 Agentic Loop 模式，持续迭代执行直到目标达成。

## 循环结构

```
# ===== 初始化阶段 =====
team = TeamCreate(
    name="loop-execution-team",
    goal="完成用户指定的迭代任务目标",
    members=["coder", "tester", "reviewer"]  # 根据任务需求动态调整
)
defer TeamDelete(team.id)

main_task = TaskCreate(
    title="Loop 主任务",
    description="用户提供的任务目标",
    acceptance_criteria=["验收标准1", "验收标准2", ...]
)

iteration = 0
stalled_count = 0        # 无进展计数器
max_stalled_attempts = 3 # 最多允许3次停滞后才询问用户

# ===== 迭代循环 =====
while True:  # 持续执行直到目标达成
    iteration += 1

    # ─────────────────────────────────────────────
    # Phase 1: Gather - 收集当前上下文
    # ─────────────────────────────────────────────
    print(f"--- 迭代 {iteration} ---")

    # 1.1 获取所有任务状态
    tasks = TaskList()
    current_status = TaskGet(main_task.id)

    # 1.2 读取代码状态、测试结果、日志
    code_state = read_current_codebase()
    test_results = check_test_results()

    # 1.3 分析上次迭代的反馈
    last_feedback = current_status.metadata.get("last_feedback", {})

    # 1.4 确定本次迭代目标和子任务
    sub_goals = plan_iteration_goals(last_feedback, test_results)


    # ─────────────────────────────────────────────
    # Phase 2: Act - 执行操作
    # ─────────────────────────────────────────────
    print(f"[Act] 执行 {len(sub_goals)} 个子目标")

    # 2.1 分配任务给 agents（并行不超过2个）
    parallel_tasks = []
    for goal in sub_goals[:2]:  # 最多2个并行
        agent_result = Agent(
            subagent_type=goal.agent_type,  # coder/tester/reviewer
            task=goal.description,
            context=goal.context
        )
        parallel_tasks.append(agent_result)

        # 2.2 更新任务状态
        TaskUpdate(
            task_id=main_task.id,
            status="in_progress",
            metadata={
                "iteration": iteration,
                "current_goal": goal.description,
                "agent_type": goal.agent_type
            }
        )

    # 2.3 等待并行任务完成
    results = wait_for_agents(parallel_tasks)


    # ─────────────────────────────────────────────
    # Phase 3: Verify - 验证结果
    # ─────────────────────────────────────────────
    print("[Verify] 验证执行结果")

    # 3.1 运行测试验证
    test_result = run_verification_tests()

    # 3.2 检查验收标准
    acceptance_check = check_acceptance_criteria(
        main_task.acceptance_criteria,
        test_result
    )

    # 3.3 更新任务验证结果
    TaskUpdate(
        task_id=main_task.id,
        metadata={
            "iteration": iteration,
            "verification_result": test_result,
            "acceptance_passed": acceptance_check.passed,
            "failed_criteria": acceptance_check.failed_items
        }
    )

    # ─────────────────────────────────────────────
    # 终止条件检查 - 成功
    # ─────────────────────────────────────────────

    # 成功：所有验收标准通过
    if acceptance_check.passed:
        print("[完成] 所有验收标准通过")
        TaskUpdate(
            task_id=main_task.id,
            status="completed",
            metadata={"total_iterations": iteration}
        )
        report_success(iteration, results)
        break


    # ─────────────────────────────────────────────
    # Phase 4: Adjust - 分析失败原因并调整策略
    # ─────────────────────────────────────────────
    print(f"[Adjust] 分析失败原因并调整策略")

    # 4.1 分析失败原因
    failure_analysis = analyze_failure(test_result, acceptance_check)

    # 4.2 检测是否停滞（相同错误重复出现）
    is_stalled = is_same_error(test_result, last_feedback)
    if is_stalled:
        stalled_count += 1
        print(f"[Adjust] 检测到停滞 ({stalled_count}/{max_stalled_attempts})")
    else:
        stalled_count = 0  # 有进展，重置计数器

    # 4.3 调整下次策略
    if is_stalled and stalled_count < max_stalled_attempts:
        # 停滞但未达到上限，尝试更激进的策略
        adjustment_strategy = decide_recovery_strategy(
            failure_analysis,
            stalled_count,
            previous_strategies=last_feedback.get("tried_strategies", [])
        )
        print(f"[Adjust] 尝试恢复策略 #{stalled_count}: {adjustment_strategy}")
    else:
        # 正常调整策略
        adjustment_strategy = decide_next_strategy(failure_analysis)

    # 4.4 记录调整策略
    TaskUpdate(
        task_id=main_task.id,
        metadata={
            "iteration": iteration,
            "last_feedback": test_result,
            "adjustment_strategy": adjustment_strategy,
            "failure_reason": failure_analysis,
            "stalled_count": stalled_count,
            "tried_strategies": last_feedback.get("tried_strategies", []) + [adjustment_strategy]
        }
    )

    print(f"[Adjust] 下次策略: {adjustment_strategy}")


    # ─────────────────────────────────────────────
    # 停滞处理 - 请求用户指导并继续
    # ─────────────────────────────────────────────

    # 停滞过多：请求用户指导
    if stalled_count >= max_stalled_attempts:
        print(f"[停滞] 连续 {stalled_count} 次无进展，请求用户指导")
        TaskUpdate(
            task_id=main_task.id,
            status="awaiting_guidance",
            metadata={
                "stalled_reason": test_result.error,
                "stalled_at_iteration": iteration,
                "tried_strategies": last_feedback.get("tried_strategies", [])
            }
        )

        # 请求用户指导
        user_guidance = AskUserQuestion(
            f"任务停滞 {stalled_count} 次，已尝试策略：\n" +
            "\n".join(f"- {s}" for s in last_feedback.get("tried_strategies", [])) +
            f"\n\n当前错误：{test_result.error}\n\n" +
            "请提供指导：\n" +
            "1. 具体的解决方向或建议\n" +
            "2. 需要调整的参数或方法\n" +
            "3. 或者输入 'continue' 让我尝试新的自动策略"
        )

        # 根据用户指导调整策略
        if user_guidance and user_guidance.lower() != 'continue':
            # 用户提供了具体指导，重置停滞计数器并应用指导
            stalled_count = 0
            adjustment_strategy = f"用户指导: {user_guidance}"
            TaskUpdate(
                task_id=main_task.id,
                metadata={
                    "user_guidance": user_guidance,
                    "adjustment_strategy": adjustment_strategy,
                    "tried_strategies": []  # 清空策略历史，开始新方向
                }
            )
            print(f"[Adjust] 应用用户指导并继续执行")
        else:
            # 用户要求继续自动尝试，重置计数器
            stalled_count = 0
            print(f"[Adjust] 用户确认继续，重置停滞计数器并尝试新策略")

        # 继续循环，不退出


# ===== 循环结束清理 =====
# 注意：此循环会持续执行直到目标达成或用户主动中断
# 不存在迭代次数上限，确保任务必须完成
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

- 在成功检查**之后**执行，确保每次失败都有机会调整
- 分析验证失败的原因
- 检测是否停滞（相同错误重复出现）
- 如果停滞但未达到上限（3次），尝试更激进的恢复策略
- 记录已尝试的策略，避免重复相同方法
- 调整下一次迭代的策略
- 连续 3 次停滞时，请求用户指导并根据反馈调整策略
- **重要**：请求用户指导后会继续循环，不会退出

## 终止条件

**Loop 模式设计原则**：必须完成全部工作直到符合预期，不存在迭代次数上限。

1. **目标达成**：所有验收标准通过 → 成功退出
2. **停滞过多**：连续 3 次迭代出现相同错误，且已尝试多种恢复策略仍无效 → 请求用户指导后继续（不退出）
3. **用户中断**：用户主动发送中断信号 → 根据用户指令处理

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
状态：成功（所有验收标准通过）
总迭代次数：N
变更摘要：[所有变更的简要列表]
停滞次数：M（如果发生过停滞）
用户指导次数：K（如果请求过用户指导）
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

## 团队管理流程（使用内置工具）

Loop 模式推荐使用 `orchestrator` Agent 作为团队领导，通过内置工具进行团队管理和任务协调。

### 团队组建流程

```
迭代开始前:
  1. 使用 TeamCreate 创建执行团队
     - 定义团队名称和目标
     - 声明所需的 agent 角色（如 coder, tester, reviewer）
     - 设置团队通信规则

  2. 使用 TaskCreate 为团队创建主任务
     - 定义任务目标和验收标准
     - 分解为可并行的子任务
     - 建立任务依赖关系（DAG）
```

### Gather 阶段的团队操作

```
[Gather] 阶段:
  1. TaskList - 列出所有待执行任务
  2. TaskGet - 获取任务详情和状态
  3. 评估团队成员能力与任务需求的匹配度
  4. 识别可并行执行的独立任务
  5. 确认团队成员的可用状态
```

### Act 阶段的任务分配

```
[Act] 阶段:
  1. 使用 Agent 工具分配任务给团队成员
     - 独立任务并行分配（不超过 2 个并行）
     - 依赖任务串行执行
     - 避免多个 agent 修改同一文件

  2. 使用 TaskUpdate 记录任务执行状态
     - 更新任务进度
     - 记录关键 metadata（如 iteration, agent_id）
     - 标记阻塞或失败状态

  3. 团队协作规范
     - coder agent 负责代码实现
     - tester agent 负责测试验证
     - reviewer agent 负责代码审查
     - orchestrator 协调冲突和依赖
```

### Verify 阶段的团队验证

```
[Verify] 阶段:
  1. 并行任务结果收集
     - 等待所有并行任务完成
     - 汇总各 agent 的执行结果

  2. 使用 TaskGet 确认任务状态
     - 检查 metadata 中的验证结果
     - 识别失败或阻塞的任务

  3. 团队输出整合
     - 合并代码变更（无冲突）
     - 运行集成测试
     - 统一验证标准
```

### Adjust 阶段的团队调整

```
[Adjust] 阶段:
  1. 分析失败原因
     - 任务失败：调整任务策略
     - agent 失败：重新分配或替换 agent
     - 依赖冲突：重新规划任务顺序

  2. 检测停滞并选择恢复策略
     - 检查是否与上次错误相同
     - 如果停滞：stalled_count += 1
     - 如果有进展：stalled_count = 0（重置）
     - 根据停滞次数选择策略：
       * 第1次：调整现有方案参数
       * 第2次：尝试替代实现方案
       * 第3次：重新分解任务或更换 agent
     - 记录已尝试的策略，避免重复

  3. 使用 TaskUpdate 记录调整策略
     - 更新 metadata.adjustment_strategy
     - 记录失败次数和原因（stalled_count）
     - 记录已尝试的策略列表（tried_strategies）

  4. 团队重组（如需要）
     - 使用 TeamDelete 解散无效团队
     - 使用 TeamCreate 创建新团队
```

### 团队协作示例

```
迭代 1:
  [Gather]
    - TeamCreate "feature-team"（成员: coder-a, coder-b, tester-c）
    - TaskCreate "实现登录功能"
    - 分解子任务: [实现 API, 实现 UI, 编写测试]

  [Act]
    - Agent(coder-a) → 实现 API（并行 1）
    - Agent(coder-b) → 实现 UI（并行 2）
    - TaskUpdate: 标记两个任务为 in_progress

  [Verify]
    - 等待 coder-a 和 coder-b 完成
    - Agent(tester-c) → 运行集成测试
    - TaskGet: 检查测试结果 → 部分失败

  [Adjust]
    - TaskUpdate: 记录失败原因（API 返回格式错误）
    - 下次迭代策略: 修复 API 格式

迭代 2:
  [Gather]
    - TaskList: 获取失败任务
    - 识别问题：API 序列化问题

  [Act]
    - Agent(coder-a) → 修复 API 序列化
    - TaskUpdate: 标记为 in_progress

  [Verify]
    - Agent(tester-c) → 重新运行测试
    - TaskGet: 测试全部通过

  [完成]
    - TaskUpdate: 标记所有任务为 completed
    - TeamDelete "feature-team"
```

## 适用场景

- 修复测试失败（迭代修复直到所有测试通过）
- 性能优化（迭代优化直到达标）
- 代码重构（迭代重构直到 lint 通过）
- 功能实现（迭代实现直到验收通过）
- 多模块并行开发（团队协作模式）
- 复杂系统集成（需要多角色配合）

## 注意事项

- **无迭代次数限制**：Loop 会持续执行直到所有验收标准通过，不存在最大迭代次数
- **必须完成**：设计原则是必须完成全部工作符合预期才停止，不允许中途放弃
- 每次迭代必须有可观测的进展
- 不要在一次迭代中做过多变更
- 保持每次迭代的上下文连贯
- **自动恢复优先**：遇到停滞时，先尝试最多3次不同的恢复策略，而非立即询问用户
- **智能调整**：每次停滞时应尝试不同的策略（调参 → 替代方案 → 重新分解），避免重复相同方法
- **记录历史**：通过 metadata.tried_strategies 记录已尝试的策略，避免循环
- **用户介入不中断**：请求用户指导后会继续执行，不会退出循环
- **用户指导后重置**：获得用户指导后重置停滞计数器，开始新的尝试方向
- 每次迭代后通过 `TaskUpdate` 更新任务状态和 metadata
