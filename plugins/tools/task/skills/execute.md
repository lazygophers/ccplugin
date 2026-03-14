---
description: 任务执行规范 - 并行编排、团队管理、进度跟踪的执行规范
model: sonnet
context: fork
user-invocable: true
---

# Skills(task:execute) - 任务执行规范

## 适用场景

- Loop 命令步骤 3：任务执行
- 需要按依赖顺序调度执行子任务
- 需要管理并行任务（最多 2 个）
- 需要跟踪任务进度

## 执行流程

### 1. 获取待执行任务

```
tasks = TaskList()
pending_tasks = [t for t in tasks if t.status == "pending"]
```

### 2. 检查依赖并识别可并行任务

对于每个待执行任务：
- 使用 `TaskGet` 获取任务详情
- 检查 `dependencies` 是否都已满足
- 识别无依赖且文件无交集的任务（可并行）

### 3. 判断执行方式并初始化

**单任务场景**：直接调用 Agent
**多任务场景**：创建 Team 并行执行

```python
if len(parallel_tasks) <= 1:
    # 单任务：直接执行
    execute_single_task(parallel_tasks[0])
else:
    # 多任务：创建 Team 并行执行
    execute_parallel_tasks(parallel_tasks)
```

### 4. 执行者复用机制

维护执行者池，优先复用已存在的执行者：

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

#### 6.1 创建 Team

```python
team_name = f"task-execution-{iteration}"
TeamCreate(team_name=team_name)
print(f"[Team 创建] {team_name}")
```

#### 6.2 分配执行者并加入 Team

```python
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

add_executors_to_team(team_name, parallel_tasks)
```

#### 6.3 监控 Team 执行进度

```python
def monitor_team_progress(team_name):
    while True:
        teammates = TeamList()
        active_executors = [t for t in teammates if t.team_name == team_name]

        if not active_executors:
            print(f"[Team 完成] {team_name} 所有执行者已完成")
            break

        # 更新任务进度
        for executor in active_executors:
            update_task_status(executor)

        # 输出进度
        print_progress_report()

        # 等待一段时间再检查
        time.sleep(5)

monitor_team_progress(team_name)
```

#### 6.4 清理 Team 和资源

```python
def cleanup_team(team_name):
    # 1. 等待所有执行者完成
    print(f"[Team 清理] {team_name} 开始清理...")

    while True:
        teammates = TeamList()
        active_executors = [t for t in teammates if t.team_name == team_name]
        if not active_executors:
            break
        time.sleep(1)

    # 2. 删除 Team
    TeamDelete()
    print(f"[Team 删除] {team_name} 已删除")

    # 3. 立即清理所有执行者的 tmux session
    cleanup_all_executors(team_name)
    print(f"[Team 清理] {team_name} 清理完成")

def cleanup_all_executors(team_name):
    # 清理该 team 关联的所有执行者的 tmux session
    for agent_type, executors in list(executor_pool.items()):
        for executor in list(executors):
            # 清理 tmux session
            index = executor['name'].split('-')[-1]
            tmux_session = f"task-exec-{agent_type.lower()}-{index}"

            try:
                subprocess.run(
                    ["tmux", "kill-session", "-t", tmux_session],
                    capture_output=True,
                    check=False
                )
                print(f"[清理] tmux session {tmux_session} 已删除")
            except Exception as e:
                print(f"[清理] tmux session {tmux_session} 清理失败: {e}")

            # 从执行者池移除
            executors.remove(executor)

    # 移除空的 agent_type
    if not executors:
        del executor_pool[agent_type]
```

### 7. 完整执行流程示例

```python
def execute_tasks(tasks, iteration):
    # 1. 识别可并行任务
    parallel_tasks = identify_parallel_tasks(tasks)

    if len(parallel_tasks) <= 1:
        # 单任务
        execute_single_task(parallel_tasks[0])
    else:
        # 多任务：完整的 Team 生命周期
        team_name = f"task-execution-{iteration}"

        # 创建 Team
        TeamCreate(team_name=team_name)

        # 分配执行者
        add_executors_to_team(team_name, parallel_tasks)

        # 监控执行
        monitor_team_progress(team_name)

        # 清理 Team
        cleanup_team(team_name)

    # 输出最终进度
    print_final_progress_report()
```

## 输出格式

### 任务进度输出

执行过程中应实时输出任务进度，格式如下：

```
[MindFlow·${任务内容}·步骤3/${迭代轮数}·running]
任务进度：
T1: 创建用户模型 ········ 已完成·············· coder-mysql
T2: 创建订单模型 ········ 进行中 ············· coder-mysql
T3: 创建商品模型 ········ 待执行(依赖 T2) ····· coder-postgres
T4: 创建库存模型 ········ 待执行(依赖 T2) ····· coder-python
T5: 创建通知模块 ········ 待执行(依赖 T4) ····· coder-python
```

**输出说明**：
- 每个任务显示：任务ID、任务描述、状态、执行者类型
- 状态包括：已完成、进行中、待执行(依赖 X)
- 使用点号和空格形成视觉进度条
- 实时更新，反映最新的任务状态

## 并行规则

1. 每一个并行任务至少包含一个前置依赖（没有则为父任务是前置依赖）
2. 依赖已满足的任务都允许被调度
3. 同时最多只有 2 个槽位执行任务
4. 槽位释放时立即检查队列，自动启动下一个 Ready 任务
5. 任务完成后重新评估所有 Blocked 任务的依赖状态

## 核心原则

- **依赖优先**：严格按依赖顺序执行
- **并行上限**：最多 2 个任务同时执行
- **执行者复用**：优先使用已存在的同类型执行者
- **精准清理**：只清理特定执行者的 tmux session，不清理所有
- **状态跟踪**：实时更新任务状态
- **Team 隔离**：每次迭代创建独立的 Team，不跨迭代复用

## ⚠️ 必须遵守的约束

1. **工作目录一致性**：Agent 必须继承 leader 的 `os.getcwd()`
	- 通过 `context` 传递 `working_directory: os.getcwd()`
	- 使用 tmux 时：`tmux new-session -d -s agent -c $(pwd)`
2. **任务创建规范**：TaskCreate 时必须在 metadata 中指定 agent_type
	- 示例：`TaskCreate(..., metadata={"agent_type": "Coder", "skills": [...]})`
	- 目的：明确任务由哪个类型的 agent 执行，便于执行者复用和调度
3. **执行者复用**：尽可能复用已创建的执行者，避免重复创建
	- 优先使用已存在且空闲的 executor（同 agent_type）
	- 仅在无可复用执行者或所有执行者忙碌时创建新的
	- **及时清理不需要的执行者**：当某类型执行者长时间空闲或不再需要时，主动清理

## 注意事项

- **Team 生命周期**：步骤 3 内创建 → 执行 → 清理，步骤结束时必须无 Team 成员
- **资源清理**：精准清理执行者关联的 tmux session
- **不要跳过**：`tmux kill-server` 会清理所有 tmux，包括用户其他会话
- **验证清理**：清理后验证 Team 已删除，tmux session 已清理
