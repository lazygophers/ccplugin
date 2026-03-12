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

### 1. 调用 Agent 执行任务

使用工具：Agent

根据任务的 metadata.agent_type 调用相应的 agent：
```
Agent(
  subagent_type=task.metadata.agent_type,  # 如 "coder", "tester"
  task=task.description,
  context={
    "target_files": task.metadata.target_files,
    "skills": task.metadata.skills,
    "acceptance_criteria": task.acceptance_criteria
  }
)
```

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

### 并行条件验证

执行前必须验证：
1. 任务无依赖关系（blockedBy 为空或已完成）
2. 当前并行数 < 2
3. target_files 无交集
4. 不修改同一模块或包

### 并行分组示例

```
当前待执行：T1, T2, T3, T4, T5
- T1, T2: 无依赖，文件无交集 → 并行组 1
- T3, T4: 依赖 T1，文件无交集 → 并行组 2（等待组 1 完成）
- T5: 依赖 T2 和 T3 → 串行（等待前置完成）

执行顺序：
1. 启动 T1 和 T2 并行执行
2. 等待 T1 和 T2 都完成
3. 启动 T3 和 T4 并行执行
4. 等待 T3 和 T4 都完成
5. 启动 T5 串行执行
```

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

## 输出要求

任务执行完成后：
1. 所有任务状态已更新为 completed 或 failed
2. 失败任务已记录失败原因
3. 进度信息已输出
4. Agent 已通过 SendMessage 上报结果

## 注意事项

- 不要跳过依赖检查直接执行
- 不要超过 2 个任务并行
- 不要忽略文件冲突检查
- Agent 遇到问题通过 SendMessage 上报，不直接提问
