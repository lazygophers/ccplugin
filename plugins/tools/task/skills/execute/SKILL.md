---
name: execute
description: 任务执行规范 - 并行编排、团队管理、进度跟踪的执行规范
user-invocable: true
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
import os

Agent(
  subagent_type=task.metadata.agent_type,
  task=task.description,
  background=True,  # 尽可能使用后台运行
  context={
    "target_files": task.metadata.target_files,
    "skills": task.metadata.skills,
    "acceptance_criteria": task.acceptance_criteria,
    "working_directory": os.getcwd()  # 继承 leader 的工作目录
  }
)
```

**多任务场景**（通过 team）：
```
import os

Agent(
  team_name="task-execution-team",
  name=f"executor-{task_id}",
  subagent_type=task.metadata.agent_type,
  task=task.description,
  background=True,  # 尽可能使用后台运行
  context={
    "target_files": task.metadata.target_files,
    "skills": task.metadata.skills,
    "acceptance_criteria": task.acceptance_criteria,
    "working_directory": os.getcwd()  # 继承 leader 的工作目录
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
   - 在每次 Agent 调用时通过 `context` 传递 `working_directory: os.getcwd()`
   - 确保 agent 访问的文件路径与 leader 相同
   - 避免相对路径解析错误

   **使用 tmux 的特殊要求**：
   - 如果使用 tmux 启动 agent，必须通过 `-c` 参数指定启动目录
   - 启动目录必须是 leader 的工作目录，不允许使用默认目录或其他目录
   - 示例：`tmux new-session -d -s agent -c $(pwd)`

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

## 并行执行控制：任务队列 + 两槽位模型

### 核心机制

```
┌─────────────────────────────────────────────────────────┐
│                      任务队列                            │
│  [所有依赖已满足的 Ready 任务]                           │
│  T2 (Ready) | T3 (Ready) | T4 (Ready) | T5 (Blocked)    │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ 从队列取出任务，填充空闲槽位
                  │
     ┌────────────┴──────────────┐
     │                           │
     ▼                           ▼
┌──────────┐                ┌──────────┐
│ Slot #1  │                │ Slot #2  │  ← 最多 2 个并行槽位
│   T2     │                │   T3     │
│ 执行中   │                │ 执行中   │
└─────┬────┘                └─────┬────┘
      │                           │
      │ T2 完成 ✓                 │ T3 仍在运行
      ▼                           │
┌──────────┐                      │
│ Slot #1  │ ← 自动补位             │
│   T4     │    (从队列取出)        │
│ 执行中   │                       │
└──────────┘                       │
                                   │ T3 完成 ✓
                                   ▼
                              ┌──────────┐
                              │ Slot #2  │ ← 自动补位
                              │   T5     │    (依赖满足后)
                              │ 执行中   │
                              └──────────┘
```

### Leader 的队列管理职责

Leader 负责：
1. **维护任务队列**：动态筛选依赖已满足的 Ready 任务
2. **管理两个槽位**：跟踪 Slot#1 和 Slot#2 的占用状态
3. **自动补位**：槽位释放时立即从队列取出下一个任务
4. **依赖检查**：每次任务完成后重新评估队列中任务的依赖状态
5. **文件冲突检查**：确保并行任务不修改同一文件

### 并行条件验证

启动任务前必须验证：
1. **依赖满足**：任务的 blockedBy 为空或已完成
2. **槽位可用**：当前并行数 < 2（有空闲槽位）
3. **文件无冲突**：target_files 与当前执行中任务无交集
4. **模块无冲突**：不修改同一模块或包

### 动态队列调度算法

```python
# 初始化两个槽位
slots = [None, None]  # Slot#1, Slot#2

while 有待执行任务:
    # 1. 更新任务队列（筛选依赖已满足的任务）
    ready_queue = []
    pending_tasks = [t for t in tasks if t.status == "pending"]
    for task in pending_tasks:
        if all_dependencies_completed(task.blockedBy):
            ready_queue.append(task)

    # 2. 填充空闲槽位（从队列取出任务）
    for i in range(2):
        if slots[i] is None and len(ready_queue) > 0:
            # 槽位空闲，从队列取出任务
            task = ready_queue.pop(0)

            # 检查文件冲突
            if no_file_conflict_with_running_tasks(task, slots):
                slots[i] = task
                start_task(task)
                print(f"[槽位#{i+1}] 启动任务 {task.id}")

    # 3. 等待任意一个任务完成
    completed_task = wait_for_any_completion(slots)

    # 4. 释放槽位（自动触发下一轮补位）
    for i in range(2):
        if slots[i] == completed_task:
            slots[i] = None
            print(f"[槽位#{i+1}] 任务完成，槽位释放")
            break
```

### 执行时间线示例

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

**执行时间线**：
```
时刻 0:
Queue: [T1✓, T2✓] [T3⊗, T4⊗, T5⊗]  ← ⊗ 表示依赖未满足
Slot#1: T1 启动
Slot#2: T2 启动

时刻 1: (T1 完成)
Queue: [T3✓] [T4⊗, T5⊗]  ← T3 依赖满足，进入队列
Slot#1: 空闲 → T3 启动 (自动补位)
Slot#2: T2 运行中

时刻 2: (T2 完成)
Queue: [T4✓] [T5⊗]  ← T4 依赖满足，进入队列
Slot#1: T3 运行中
Slot#2: 空闲 → T4 启动 (自动补位)

时刻 3: (T3 完成)
Queue: [] [T5⊗]  ← T5 依赖未满足（还需等待 T4）
Slot#1: 空闲 (等待)
Slot#2: T4 运行中

时刻 4: (T4 完成)
Queue: [T5✓]  ← T5 依赖满足，进入队列
Slot#1: 空闲 → T5 启动 (自动补位)
Slot#2: 空闲

时刻 5: (T5 完成)
Queue: []
Slot#1: 空闲
Slot#2: 空闲
→ 所有任务完成
```

**调度逻辑总结**：
- ✓ 表示依赖已满足（Ready）
- ⊗ 表示依赖未满足（Blocked）
- 槽位释放时立即检查队列，自动补位
- 任务完成后重新评估所有 Blocked 任务的依赖状态

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

**⚠️ 必须执行**：步骤 4 结束时，无论任务成功或失败，都必须删除 team。

```
# 删除团队（如果创建了）
if team_id is not None:
    TeamDelete(team_id)
    team_id = None
    print("[清理] Team 已删除")
```

**检查点**：
- 如果进入步骤 5（结果验证）时仍能看到 `@executor-*` 成员
- 说明此清理步骤未执行，必须立即执行 TeamDelete

## 输出要求

任务执行完成后：
1. 所有任务状态已更新为 completed 或 failed
2. 失败任务已记录失败原因
3. 进度信息已输出
4. Agent 已通过 SendMessage 上报结果
5. **Team 已删除**（如果创建了）- 此时不应存在任何 team 成员

## 注意事项

- 不要跳过依赖检查直接执行
- 不要超过 2 个任务并行
- 不要忽略文件冲突检查
- Agent 遇到问题通过 SendMessage 上报，不直接提问