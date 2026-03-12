---
name: execute
description: 任务执行规范 - 并行编排、团队管理、进度跟踪的执行规范
user-invocable: false
context: fork
---

# 任务执行规范

任务执行是 loop 循环的第四步，负责按计划调度执行所有子任务，支持并行/串行编排。

## 执行目标

- 按依赖顺序调度子任务执行
- 管理并行/串行任务编排
- 跟踪任务进度和状态
- 处理执行失败和异常

## 执行步骤

### 0. 判断是否创建团队

使用工具：TaskList, TeamCreate

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

### 1. 调用 Agent 执行任务

使用工具：Agent

根据任务数量选择调用方式：

**单任务场景**（不创建 team）：
```
Agent(
  subagent_type=task.metadata.agent_type,
  task=task.description,
  background=True,  # 尽可能使用后台运行
  context={
    "target_files": task.metadata.target_files,
    "skills": task.metadata.skills,
    "acceptance_criteria": task.acceptance_criteria
  }
)
```

**多任务场景**（通过 team）：
```
Agent(
  team_name="task-execution-team",
  name=f"executor-{task_id}",
  subagent_type=task.metadata.agent_type,
  task=task.description,
  background=True,  # 尽可能使用后台运行
  context={
    "target_files": task.metadata.target_files,
    "skills": task.metadata.skills,
    "acceptance_criteria": task.acceptance_criteria
  }
)
```

**后台运行要求**：
- 所有 agent 尽可能使用 `background=True` 在后台运行
- 后台运行可以提升执行效率，减少主线程阻塞
- 只有需要实时交互的 agent 才使用前台模式

Agent 职责：
- 执行具体的任务实现
- 通过 SendMessage 上报结果或问题给 leader
- 不直接调用 AskUserQuestion
- 不调用其他 agents

### 2. 并行/串行调度

使用工具：TaskList, TaskGet, TaskUpdate

调度策略：
1. 使用 TaskList 获取所有待执行任务
2. 使用 TaskGet 检查任务的依赖关系（blockedBy）
3. 识别可并行的任务（无依赖、文件无交集）
4. 最多同时执行 2 个任务
5. 等待并行任务完成后再进入下一组

依赖检查：
```
task = TaskGet(task_id)
if not task.blockedBy:
    # 无依赖，可以执行
if all_dependencies_completed(task.blockedBy):
    # 依赖已完成，可以执行
```

文件冲突检查：
```
# 检查并行任务的 target_files 无交集
task_a_files = set(task_a.metadata.target_files)
task_b_files = set(task_b.metadata.target_files)
if task_a_files.isdisjoint(task_b_files):
    # 可以并行
```

### 3. 更新任务状态

使用工具：TaskUpdate

状态转换：
- 开始执行：`TaskUpdate(task_id, status="in_progress")`
- 执行成功：`TaskUpdate(task_id, status="completed")`
- 执行失败：`TaskUpdate(task_id, status="failed", metadata={"failure_reason": "..."})`

进度跟踪：
```
TaskUpdate(
  task_id=task_id,
  metadata={
    "started_at": timestamp,
    "iteration": current_iteration,
    "retry_count": retry_count
  }
)
```

### 4. 处理 SendMessage

使用工具：SendMessage（接收）

Leader 接收来自 agents 的消息：
- **成功完成**：Agent 上报任务完成
- **遇到问题**：Agent 上报需要确认的问题
- **请求指导**：Agent 请求技术指导

Leader 处理：
- 验证完成情况
- 统一使用 AskUserQuestion 向用户提问
- 通过 SendMessage 回复 agent 指导

## 并行执行控制

### Leader 的队列管理职责

Leader 负责：
1. 维护任务执行队列
2. 跟踪所有任务状态
3. 动态检查依赖关系
4. 自动启动可执行任务
5. 保持最多 2 个任务并行

### 并行条件验证

启动任务前必须验证：
1. 任务依赖已满足（blockedBy 为空或已完成）
2. 当前并行数 < 2
3. target_files 与当前执行中任务无交集
4. 不修改同一模块或包

### 动态队列调度

```python
while 有待执行任务:
    # 1. 获取当前执行中的任务数
    running_tasks = [t for t in tasks if t.status == "in_progress"]

    # 2. 如果未达到并行上限，查找可启动任务
    if len(running_tasks) < 2:
        pending_tasks = [t for t in tasks if t.status == "pending"]
        for task in pending_tasks:
            # 检查依赖是否满足
            if all_dependencies_completed(task.blockedBy):
                # 检查文件冲突
                if no_file_conflict_with_running_tasks(task):
                    # 启动任务
                    start_task(task)
                    if len(running_tasks) >= 2:
                        break

    # 3. 等待任务完成，触发下一轮检查
    wait_for_any_task_completion()
```

### 动态队列执行示例

**依赖关系 DAG**：
```
       ┌─────────────┐  ┌─────────────┐
       │ T1: 创建模型 │  │ T2: 实现工具 │
       │ (无依赖)    │  │ (无依赖)    │
       └──────┬──────┘  └──────┬──────┘
              │                │
              ↓                ↓
       ┌─────────────┐  ┌─────────────┐
       │ T3: API接口  │  │ T4: 数据处理 │
       │ (依赖 T1)   │  │ (依赖 T2)   │
       └──────┬──────┘  └──────┬──────┘
              │                │
              └────────┬───────┘
                       ↓
                ┌─────────────┐
                │ T5: 集成测试 │
                │(依赖 T3,T4) │
                └─────────────┘
```

**执行队列**（最多同时 2 个）：
```
时刻 0: [T1 执行中] [T2 执行中] [T3 等待] [T4 等待] [T5 等待]
时刻 1: [T1 完成✓] [T2 执行中] [T3 执行中] [T4 等待] [T5 等待]
时刻 2: [T1 完成✓] [T2 完成✓] [T3 执行中] [T4 执行中] [T5 等待]
时刻 3: [T1 完成✓] [T2 完成✓] [T3 完成✓] [T4 完成✓] [T5 执行中]
```

**调度逻辑**：
- 初始启动无依赖任务（T1, T2）
- 任务完成后，检查队列中依赖已满足的任务
- 自动启动可执行任务，保持最多 2 个并行

## 失败处理

### 失败升级策略

- 第 1 次失败：TaskUpdate 记录失败原因，调用 Agent 重试
- 第 2 次失败：调用调试类 Agent 深入诊断
- 第 3 次失败：重新分析任务定义，考虑重新规划
- 仍然失败：AskUserQuestion 请求用户指导

失败记录：
```
TaskUpdate(
  task_id=task_id,
  status="failed",
  metadata={
    "failure_reason": "...",
    "retry_count": retry_count,
    "last_error": error_message
  }
)
```

## 进度输出

执行过程中实时输出进度：
```
[进度] T1 实现用户模型 ......... 已完成 ✓
[进度] T2 实现 API 接口 ......... 执行中
[进度] T3 编写单元测试 ......... 待执行
[进度] T4 集成测试 ............. 待执行

总进度：1/4 (25%)
```

## 执行完成后清理

使用工具：TeamDelete

```
# 删除团队（如果创建了）
if team_id is not None:
    TeamDelete(team_id)
    team_id = None
```

## 输出要求

任务执行完成后：
1. 所有任务状态已更新为 completed 或 failed
2. 失败任务已记录失败原因
3. 进度信息已输出
4. Agent 已通过 SendMessage 上报结果
5. **Team 已删除**（如果创建了）

## 注意事项

- 不要跳过依赖检查直接执行
- 不要超过 2 个任务并行
- 不要忽略文件冲突检查
- Agent 遇到问题通过 SendMessage 上报，不直接提问
