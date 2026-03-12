---
name: loop
description: 循环控制规范 - 6 步循环流程、迭代策略、终止条件和团队管理
user-invocable: false
context: fork
---

# 循环控制规范

定义 /loop 命令的完整执行流程和控制规范。Loop 命令作为 team leader 负责所有调度和管理工作。

## 循环流程（6 步）

```
1. 信息收集 → 2. 计划设计 → 3. 计划确认
                                    ↓
                           4. 任务执行
                                    ↓
                           5. 结果验证
                                    ↓
                           6. 失败调整 → 回到步骤 2（如需要）
```

## 初始化阶段

Loop 开始时执行一次：

```
# 创建主任务
TaskCreate(
  title="Loop 主任务",
  description="用户提供的任务目标",
  acceptance_criteria=["验收标准1", "验收标准2", ...]
)

# 初始化迭代状态
iteration = 0
stalled_count = 0  # 停滞计数器
max_stalled_attempts = 3  # 最多允许 3 次停滞
team_id = None  # 团队 ID，仅在执行多任务时创建
```

## 步骤 1：信息收集

使用 Skills(task:gather) 规范执行。

执行内容：
- 使用 Read, Glob, Grep 读取项目文件
- 使用 Agent(subagent_type='Explore') 或其他 agent 收集信息
- 通过 AskUserQuestion 确认不确定部分（仅 leader 可用）

输出：
- 完整的需求理解
- 项目技术栈和架构
- 相关文件和模块列表
- 技术约束和规范要求

## 步骤 2：计划设计

使用 Skills(task:plan) 规范执行。

执行内容：
- 使用 TaskCreate 分解任务为原子子任务
- 使用 TaskUpdate addBlockedBy 建立依赖关系
- 为每个任务分配 agent_type 和 skills
- 可选：使用 Agent 调用规划类 agent 辅助规划

输出：
- 所有子任务已注册（TaskCreate）
- 依赖关系已建立（TaskUpdate）
- 每个任务包含 metadata（target_files, agent_type, skills）

## 步骤 3：计划确认

执行内容：
- 输出任务列表（包含依赖关系）
- 输出验收标准
- 输出简要说明（≤100字）
- 使用 AskUserQuestion 让用户确认计划

示例输出格式：
```
## 执行计划

### 执行流程图

**依赖关系 DAG**：
```
       ┌─────────────────────┐  ┌─────────────────────┐
       │ T1: 实现用户模型     │  │ T2: 实现工具模块     │
       │ agent: coder        │  │ agent: coder        │
       │ files: user.py      │  │ files: helper.py    │
       │ (无依赖)            │  │ (无依赖)            │
       └──────────┬──────────┘  └──────────┬──────────┘
                  │                        │
                  ↓                        ↓
       ┌─────────────────────┐  ┌─────────────────────┐
       │ T3: 实现 API 接口    │  │ T4: 实现数据处理     │
       │ agent: coder        │  │ agent: coder        │
       │ files: auth.py      │  │ files: processor.py │
       │ (依赖 T1)           │  │ (依赖 T2)           │
       └──────────┬──────────┘  └──────────┬──────────┘
                  │                        │
                  └──────────┬─────────────┘
                             ↓
                  ┌─────────────────────┐
                  │ T5: 编写集成测试     │
                  │ agent: tester       │
                  │ files: test_*.py    │
                  │ (依赖 T3 和 T4)      │
                  └─────────────────────┘
```

**动态执行队列**（最多同时 2 个任务）：
```
时刻 0: [T1 执行中] [T2 执行中] [T3 等待T1] [T4 等待T2] [T5 等待T3,T4]
时刻 1: [T1 完成✓] [T2 执行中] [T3 执行中] [T4 等待T2] [T5 等待T3,T4]
时刻 2: [T1 完成✓] [T2 完成✓] [T3 执行中] [T4 执行中] [T5 等待T3,T4]
时刻 3: [T1 完成✓] [T2 完成✓] [T3 完成✓] [T4 完成✓] [T5 执行中]
时刻 4: 全部完成 ✓
```

**执行逻辑**：
- 初始启动所有无依赖任务（T1, T2），最多 2 个并行
- 当任务完成时，检查队列中被阻塞的任务
- 自动启动依赖已满足的任务（T1完成→T3启动，T2完成→T4启动）
- 保持最多 2 个任务并行执行

### 验收标准
- [ ] 所有测试通过
- [ ] Lint 无错误
- [ ] 功能符合需求

### 简要说明
分 5 个子任务实现用户认证功能。执行队列动态调度：T1/T2 并行启动→完成后自动启动 T3/T4→最后执行 T5 集成测试。
```

用户确认后继续。

## 步骤 4：任务执行

使用 Skills(task:execute) 规范执行。

执行内容：
1. 使用 TaskList 获取待执行任务
2. 判断任务数量：
   - 如果只有 1 个任务：直接使用 Agent 执行，不创建 team
   - 如果有多个任务：创建 team 管理并行/串行执行
3. 使用 TaskGet 检查依赖关系
4. 使用 Agent 调用相应的 agent 执行任务
5. 并行/串行调度（最多 2 个并行，文件无交集）
6. 使用 TaskUpdate 更新任务状态
7. 处理 SendMessage（接收 agent 上报）
8. **执行完成后删除 team**（如果创建了）

TeamCreate 逻辑：
```
tasks = TaskList()
pending_tasks = [t for t in tasks if t.status == "pending"]

if len(pending_tasks) > 1:
    # 多任务，创建 team
    team_id = TeamCreate(
        name="task-execution-team",
        goal="执行多个并行/串行任务"
    )
else:
    # 单任务，不创建 team
    team_id = None
```

Agent 执行示例：
```
import os

# 单任务场景：直接调用
Agent(
  subagent_type=task.metadata.agent_type,
  task=task.description,
  background=True,  # 尽可能使用后台运行
  context={
    "working_directory": os.getcwd(),  # 继承 leader 的工作目录
    ...
  }
)

# 多任务场景：通过 team 调用
Agent(
  team_name="task-execution-team",
  name=f"executor-{task_id}",
  subagent_type=task.metadata.agent_type,
  task=task.description,
  background=True,  # 尽可能使用后台运行
  context={
    "working_directory": os.getcwd(),  # 继承 leader 的工作目录
    ...
  }
)
```

**执行要求**：

1. **后台运行**：
   - 所有 agent 尽可能使用 `background=True` 在后台运行
   - 后台运行可以提升执行效率，减少主线程阻塞
   - 只有需要实时交互的 agent 才使用前台模式

2. **工作目录一致性**（⚠️ 必须遵守）：
   - Agent 的工作目录必须与 team leader 完全一致
   - 通过 `context` 传递 `working_directory: os.getcwd()`
   - 确保 agent 访问的文件路径与 leader 相同

   **使用 tmux 的特殊要求**：
   - 如果使用 tmux 启动 agent，必须通过 `-c` 参数指定启动目录
   - 启动目录必须是 leader 的工作目录，不允许使用默认目录或其他目录
   - 示例：`tmux new-session -d -s agent -c $(pwd)`

执行完成后清理（**必须执行**）：
```
# 删除团队（如果创建了）
if team_id is not None:
    TeamDelete(team_id)
    team_id = None
    print("[清理] Team 已删除")
```

**⚠️ 重要**：步骤 4 结束时必须删除 team。如果进入步骤 5 时仍能看到 `@executor-*` 成员，说明此清理步骤未执行。

实时输出进度：
```
[进度] T1 实现用户模型 ......... 已完成 ✓
[进度] T2 实现 API 接口 ......... 执行中
[进度] T3 编写测试 ............. 待执行

总进度：1/3 (33%)
```

## 步骤 5：结果验证

**前置条件**：Team 已在步骤 4 结束时删除，此时不应存在任何 team 成员。

使用 Skills(task:verify) 规范执行。

执行内容：
- 使用 TaskList, TaskGet 检查所有任务
- 验证每个任务的验收标准
- 使用 TaskUpdate 记录验证结果

验证示例：
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

判断：
- 全部通过 → Loop 完成
- 部分失败 → 进入步骤 6

## 步骤 6：失败调整

执行内容：
- 分析失败原因
- 检测是否停滞（相同错误重复）
- 决定下一步策略

停滞检测：
```
if is_same_error(current_error, last_error):
    stalled_count += 1
else:
    stalled_count = 0  # 有进展，重置
```

失败升级策略：
- 第 1 次失败：调整后重试
- 第 2 次失败：使用调试类 agent 诊断
- 第 3 次失败：重新规划任务
- 仍然失败：AskUserQuestion 请求用户指导

停滞处理（连续 3 次停滞）：
```
if stalled_count >= max_stalled_attempts:
    user_guidance = AskUserQuestion(
        "任务停滞 3 次，已尝试策略：...\n当前错误：...\n请提供指导"
    )

    if user_guidance:
        stalled_count = 0  # 重置停滞计数器
        # 应用用户指导

    # 继续循环，不退出
```

调整后：回到步骤 2 重新规划。

## 终止条件

| 条件 | 触发 | 行为 |
|------|------|------|
| 目标达成 | 步骤 5 全部通过 | 正常退出，输出报告 |
| 停滞过多 | 连续 3 次相同错误 | 请求用户指导后继续（不退出） |
| 用户中断 | 用户主动中断 | 根据用户指令处理 |

重要：
- 无最大迭代次数限制
- 停滞时请求用户指导，但不退出循环
- 获得用户指导后重置停滞计数器，继续执行

## 团队管理

### 团队生命周期

```
步骤 4（任务执行）开始：
  判断任务数量
  如果有多个任务：TeamCreate(name="task-execution-team", goal="...")
  如果只有 1 个任务：不创建 team

步骤 4 执行中：
  调用 Agent 执行任务（单任务直接调用，多任务通过 team）
  Members 通过 SendMessage 上报给 leader
  Leader 处理消息并决策

步骤 4 结束：
  如果创建了 team：TeamDelete(team_id)
```

### Leader 职责

作为 team leader，/loop 命令负责：
1. 创建和管理团队（TeamCreate/TeamDelete）
2. 调度所有工作（包括但不限于 6 步流程）
3. 接收处理 SendMessage
4. 统一执行 AskUserQuestion
5. 编排任务执行顺序

### 通信规范

- **Agent → Leader**：通过 SendMessage 上报
- **Leader → User**：通过 AskUserQuestion 提问
- **Agent 不直接提问**：遇到问题上报给 leader

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

最终输出：
```
=== Loop 完成 ===
状态：成功（所有验收标准通过）
总迭代次数：N
变更文件：[文件列表]
停滞次数：M（如发生过）
用户指导次数：K（如请求过）
```

## 清理阶段

Loop 结束时：
```
# 确认 team 已在步骤 4 删除（此时不应存在 team）
# 如果仍能看到 @executor-* 成员，说明步骤 4 清理未执行
# 输出最终报告
```

**⚠️ 检查点**：如果此时仍能看到 team 成员，必须执行 TeamDelete 补救。

## 注意事项

- 每个步骤严格按顺序执行
- 不要跳过计划确认步骤
- 并行任务数不超过 2
- 停滞时必须请求用户指导，但继续循环
- 所有提问统一通过 leader 的 AskUserQuestion
