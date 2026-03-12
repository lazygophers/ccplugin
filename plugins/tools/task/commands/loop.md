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
TeamCreate()
defer TeamDelete()

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

  2. 使用 TaskUpdate 记录调整策略
     - 更新 metadata.adjustment_strategy
     - 记录失败次数和原因

  3. 团队重组（如需要）
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

- 每次迭代必须有可观测的进展
- 不要在一次迭代中做过多变更
- 保持每次迭代的上下文连贯
- 遇到需要用户决策的问题时立即中断循环
- 每次迭代后通过 `TaskUpdate` 更新任务状态和 metadata
