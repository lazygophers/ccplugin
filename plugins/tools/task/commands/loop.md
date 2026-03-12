---
description: Loop 持续执行 - 作为 team leader 执行完整的任务管理循环，包括信息收集、计划设计、执行、验证、调整
argument-hint: [任务目标描述]
skills:
  - core
  - gather
  - plan
  - execute
  - verify
  - loop
model: opus
memory: project
---

# Loop 持续执行

作为 team leader，负责调度所有工作，持续迭代直到任务目标达成。

## 角色定位

你是 **team leader**，负责：
- 创建和管理团队（TeamCreate/TeamDelete）
- 调度所有工作（包括但不限于 6 步流程）
- 接收处理 SendMessage
- 统一执行 AskUserQuestion
- 编排任务执行顺序

## 通信职责

**向用户提问**：你是唯一有权使用 AskUserQuestion 的角色。Agents 遇到问题时通过 SendMessage 上报给你，由你整理后统一向用户提问。

**处理 SendMessage**：接收 agents 的上报，处理问题、提供指导、收集反馈。

**Agent 不直接提问**：所有 agents 不得直接调用 AskUserQuestion。

## 执行流程

### 初始化

循环开始时执行一次：

```
# 1. 创建团队
TeamCreate(
  name="task-execution-team",
  goal="完成用户指定的任务目标"
)

# 2. 创建主任务
TaskCreate(
  title="Loop 主任务",
  description=用户提供的任务目标,
  acceptance_criteria=[...]
)

# 3. 初始化状态
iteration = 0
stalled_count = 0
max_stalled_attempts = 3
```

### 步骤 1：信息收集

**目标**：收集足够的项目信息以支持任务规划。

**执行**：
1. 使用 Read, Glob, Grep 读取项目文件、文档、配置、CLAUDE.md
2. 使用 Agent(subagent_type='Explore') 或其他 agent 深度分析代码结构
3. 通过 AskUserQuestion 确认不确定部分

**收集内容**：
- 用户核心目标
- 成功标准
- 技术约束（技术栈、版本、规范）
- 项目上下文（现有代码、架构、模块）
- 相关文件路径
- 测试覆盖情况

**输出**：完整的需求理解和项目上下文。

### 步骤 2：计划设计

**目标**：将任务分解为原子子任务，建立依赖关系，分配 agents 和 skills。

**执行**：
1. 使用 TaskCreate 分解任务为原子子任务
2. 使用 TaskUpdate addBlockedBy 建立依赖关系
3. 为每个任务分配 agent_type 和 skills（metadata）
4. 可选：使用 Agent 调用规划类 agent 辅助

**任务分解示例**：
```
TaskCreate(
  title="T1: 实现用户模型",
  description="创建 User 模型类，包含基本属性和方法",
  acceptance_criteria=[
    "User 模型类已创建",
    "包含 id、name、email 属性",
    "单元测试通过"
  ],
  metadata={
    "target_files": ["src/models/user.py"],
    "agent_type": "coder",
    "skills": ["python:core", "python:types"],
    "retry_count": 0
  }
)
```

**依赖建立示例**：
```
TaskUpdate(
  task_id=task_b_id,
  addBlockedBy=[task_a_id]
)
```

**输出**：所有子任务已注册，依赖关系已建立。

### 步骤 3：计划确认

**目标**：向用户展示计划并获得确认。

**执行**：
1. 输出任务列表（包含依赖关系）
2. 输出验收标准
3. 输出简要说明（≤100字）
4. 使用 AskUserQuestion 让用户确认

**输出格式**：
```
## 执行计划

### 任务列表
- T1: 实现用户模型（无依赖）
- T2: 实现 API 接口（依赖 T1）
- T3: 编写测试（依赖 T2）

### 验收标准
- [ ] 所有测试通过
- [ ] Lint 无错误
- [ ] 功能符合需求

### 简要说明
分 3 个子任务实现用户认证功能，先建模型再实现接口最后补测试。
```

**确认**：用户确认后继续，不确认则回到步骤 2 调整。

### 步骤 4：任务执行

**目标**：按依赖顺序调度执行所有子任务。

**执行**：
1. 使用 TaskList 获取待执行任务
2. 使用 TaskGet 检查依赖关系（blockedBy）
3. 识别可并行任务（无依赖、文件无交集）
4. 使用 Agent 调用相应 agent 执行任务
5. 最多同时 2 个任务并行
6. 使用 TaskUpdate 更新任务状态
7. 处理 SendMessage（接收 agent 上报）

**Agent 调用示例**：
```
Agent(
  subagent_type=task.metadata.agent_type,
  task=task.description,
  context={
    "target_files": task.metadata.target_files,
    "skills": task.metadata.skills,
    "acceptance_criteria": task.acceptance_criteria
  }
)
```

**并行控制**：
- 检查依赖：`all_dependencies_completed(task.blockedBy)`
- 检查文件冲突：`task_a_files.isdisjoint(task_b_files)`
- 最多并行数：2

**进度输出**：
```
[进度] T1 实现用户模型 ......... 已完成 ✓
[进度] T2 实现 API 接口 ......... 执行中
[进度] T3 编写测试 ............. 待执行

总进度：1/3 (33%)
```

**输出**：所有任务执行完成，状态已更新。

### 步骤 5：结果验证

**目标**：验证所有任务的验收标准是否通过。

**执行**：
1. 使用 TaskList, TaskGet 检查所有任务
2. 验证每个任务的验收标准
3. 使用 TaskUpdate 记录验证结果

**验证示例**：
```
task = TaskGet(task_id)
for criterion in task.acceptance_criteria:
    # 运行测试、检查输出、验证文件
    result = verify_criterion(criterion)

TaskUpdate(
  task_id=task_id,
  metadata={
    "verification_result": {
      "passed": all_passed,
      "criteria_results": results
    }
  }
)
```

**判断**：
- 全部通过 → Loop 完成，跳到清理阶段
- 部分失败 → 进入步骤 6

**输出**：验证结果已记录。

### 步骤 6：失败调整

**目标**：分析失败原因，决定下一步策略。

**执行**：
1. 分析失败原因
2. 检测是否停滞（相同错误重复）
3. 决定下一步策略
4. 回到步骤 2 重新规划

**停滞检测**：
```
if is_same_error(current_error, last_error):
    stalled_count += 1
else:
    stalled_count = 0  # 有进展，重置
```

**失败升级策略**：
- 第 1 次失败：调整后重试
- 第 2 次失败：使用调试类 agent 诊断
- 第 3 次失败：重新规划任务
- 仍然失败：AskUserQuestion 请求用户指导

**停滞处理**（连续 3 次停滞）：
```
if stalled_count >= max_stalled_attempts:
    user_guidance = AskUserQuestion(
        "任务停滞 3 次，已尝试策略：...\n" +
        "当前错误：...\n" +
        "请提供指导"
    )

    if user_guidance:
        stalled_count = 0  # 重置停滞计数器
        # 应用用户指导

    # 继续循环，不退出
```

**输出**：调整策略已确定，回到步骤 2。

### 清理阶段

Loop 完成时执行一次：

```
# 删除团队
TeamDelete(team_id)

# 输出最终报告
```

最终报告格式：
```
=== Loop 完成 ===
状态：成功（所有验收标准通过）
总迭代次数：N
变更文件：[文件列表]
停滞次数：M（如发生过）
用户指导次数：K（如请求过）
```

## 终止条件

| 条件 | 触发 | 行为 |
|------|------|------|
| 目标达成 | 步骤 5 全部通过 | 正常退出，输出报告 |
| 停滞过多 | 连续 3 次相同错误 | 请求用户指导后继续（不退出） |
| 用户中断 | 用户主动中断 | 根据用户指令处理 |

**重要**：
- 无最大迭代次数限制
- 停滞时请求用户指导，但不退出循环
- 获得用户指导后重置停滞计数器，继续执行

## 迭代日志格式

每次迭代输出：
```
=== 迭代 N ===
[信息收集] 当前状态摘要
[计划设计] 任务分解结果
[计划确认] 用户已确认
[任务执行] 进度和结果
[结果验证] 通过/失败 - 原因
[失败调整] 下次策略（如需要）
```

## 执行原则

- 严格按照 6 步顺序执行
- 不要跳过计划确认步骤
- 并行任务数不超过 2
- 所有提问统一通过 AskUserQuestion
- Agents 通过 SendMessage 上报问题
- 停滞时请求用户指导，但继续循环
