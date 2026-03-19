---
description: 任务执行规范 - 并行编排、团队管理、进度跟踪的执行规范
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:execute) - 任务执行规范

<overview>

本规范定义了 Loop 命令中任务执行（Execution / Do）阶段的行为。该阶段负责将计划设计阶段产出的子任务按依赖顺序调度执行，支持最多 2 个任务并行，并通过 Team 机制管理多 agent 协作。

执行阶段的核心挑战在于平衡并行效率与资源管理。单任务场景直接调用 Agent 即可，多任务场景则需要创建 Team、分配执行者、监控进度、清理资源的完整生命周期管理。执行者复用机制避免重复创建同类型 agent，提高资源利用率。

</overview>

<execution_flow>

## 执行流程

### 1. 获取待执行任务

```
tasks = TaskList()
pending_tasks = [t for t in tasks if t.status == "pending"]
```

### 2. 检查依赖并识别可并行任务

对于每个待执行任务，使用 TaskGet 获取任务详情，检查 dependencies 是否都已满足，识别无依赖且文件无交集的任务作为可并行候选。

### 3. 判断执行方式并初始化

```python
if len(parallel_tasks) <= 1:
    # 单任务：直接执行
    execute_single_task(parallel_tasks[0])
else:
    # 多任务：创建 Team 并行执行
    execute_parallel_tasks(parallel_tasks)
```

### 4. 执行者复用机制

维护执行者池，优先复用已存在的同类型空闲执行者，仅在无可用执行者时创建新的。这样做是因为创建新 agent 有初始化开销，复用可以显著减少延迟。

```python
executor_pool = {}  # {agent_type: [{name, status, task_id, idle_since}]}

def assign_task(task):
    agent_type = task.metadata.get("agent_type", "Coder")

    # 1. 查找空闲的同类型执行者
    if agent_type in executor_pool:
        for executor in executor_pool[agent_type]:
            if executor["status"] == "idle":
                executor["status"] = "busy"
                executor["task_id"] = task.id
                print(f"[复用] 执行者 {executor['name']} → 任务 {task.id}")
                return executor["name"]

    # 2. 创建新执行者
    if agent_type not in executor_pool:
        executor_pool[agent_type] = []

    executor_index = len(executor_pool[agent_type]) + 1
    executor_name = f"executor-{agent_type.lower()}-{executor_index}"

    executor_pool[agent_type].append({
        "name": executor_name,
        "status": "busy",
        "task_id": task.id
    })

    print(f"[新建] 执行者 {executor_name} → 任务 {task.id}")
    return executor_name
```

### 5. 单任务执行

```python
def execute_single_task(task):
    agent_type = task.metadata.get("agent_type", "Coder")

    Agent(
        subagent_type=agent_type,
        prompt=task.description,
        background=True,
        context={"working_directory": os.getcwd()}
    )
```

### 6. 多任务并行执行（Team 生命周期）

多任务场景的 Team 生命周期分为四步：创建 Team、分配执行者、监控进度、清理资源。Team 在每次迭代中独立创建，不跨迭代复用，确保状态隔离。

```python
# 6.1 创建 Team
team_name = f"task-execution-{iteration}"
TeamCreate(team_name=team_name)

# 6.2 分配执行者并加入 Team
def add_executors_to_team(team_name, tasks):
    for task in tasks:
        agent_type = task.metadata.get("agent_type", "Coder")
        executor_name = assign_task(task)

        Agent(
            subagent_type=agent_type,
            name=executor_name,
            team_name=team_name,
            prompt=task.description,
            background=True,
            context={"working_directory": os.getcwd()}
        )

# 6.3 监控 Team 执行进度
def monitor_team_progress(team_name):
    while True:
        teammates = TeamList()
        active_executors = [t for t in teammates if t.team_name == team_name]

        if not active_executors:
            print(f"[Team 完成] {team_name} 所有执行者已完成")
            break

        update_task_status(executor)
        print_progress_report()
        time.sleep(5)

# 6.4 清理 Team 和资源
def cleanup_team(team_name):
    # 等待所有执行者完成
    while True:
        teammates = TeamList()
        active_executors = [t for t in teammates if t.team_name == team_name]
        if not active_executors:
            break
        time.sleep(1)

    # 删除 Team
    TeamDelete()

    # 清理该 team 关联的所有执行者的 tmux session
    for agent_type, executors in list(executor_pool.items()):
        for executor in list(executors):
            index = executor['name'].split('-')[-1]
            tmux_session = f"task-exec-{agent_type.lower()}-{index}"
            try:
                subprocess.run(
                    ["tmux", "kill-session", "-t", tmux_session],
                    capture_output=True, check=False
                )
            except Exception as e:
                print(f"[清理] tmux session {tmux_session} 清理失败: {e}")
            executors.remove(executor)
```

### 7. 完整执行流程

```python
def execute_tasks(tasks, iteration):
    parallel_tasks = identify_parallel_tasks(tasks)

    if len(parallel_tasks) <= 1:
        execute_single_task(parallel_tasks[0])
    else:
        team_name = f"task-execution-{iteration}"
        TeamCreate(team_name=team_name)
        add_executors_to_team(team_name, parallel_tasks)
        monitor_team_progress(team_name)
        cleanup_team(team_name)

    print_final_progress_report()
```

</execution_flow>

<output_format>

## 输出格式

执行过程中实时输出任务进度，每个任务显示 ID、描述、状态和执行者类型：

```
[MindFlow·${任务内容}·任务执行/${迭代轮数}·running]
任务进度：
T1: 创建用户模型 ········ 已完成·············· coder-mysql
T2: 创建订单模型 ········ 进行中 ············· coder-mysql
T3: 创建商品模型 ········ 待执行(依赖 T2) ····· coder-postgres
T4: 创建库存模型 ········ 待执行(依赖 T2) ····· coder-python
T5: 创建通知模块 ········ 待执行(依赖 T4) ····· coder-python
```

</output_format>

<rules>

## 并行规则

每个并行任务至少包含一个前置依赖（没有则父任务为前置依赖）。依赖已满足的任务可以被调度，同时最多 2 个槽位执行任务。槽位释放时立即检查队列，自动启动下一个 Ready 任务。任务完成后重新评估所有 Blocked 任务的依赖状态。

## 必须遵守的约束

工作目录一致性：Agent 必须继承 leader 的 os.getcwd()，通过 context 传递 working_directory，使用 tmux 时用 `tmux new-session -d -s agent -c $(pwd)`。

任务创建规范：TaskCreate 时必须在 metadata 中指定 agent_type，例如 `TaskCreate(..., metadata={"agent_type": "Coder", "skills": [...]})`，这样便于执行者复用和调度。

执行者复用：优先使用已存在且空闲的 executor（同 agent_type），仅在无可复用执行者时创建新的，当某类型执行者长时间空闲或不再需要时主动清理。

Team 生命周期：任务执行阶段内创建 → 执行 → 清理，阶段结束时必须无 Team 成员。资源清理要精准——只清理执行者关联的 tmux session，不要使用 tmux kill-server（会影响用户其他会话）。清理后验证 Team 已删除、tmux session 已清理。

</rules>
