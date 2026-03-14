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

### 3. 判断执行方式

- **单个任务**：直接调用对应的 Agent
- **多个任务**：创建 Team 并行执行

### 4. 执行者复用机制

维护执行者池，优先复用已存在的执行者：

```python
executor_pool = {}  # {agent_type: [{name, status, task_id}]}

def assign_task(task):
    agent_type = task.metadata.get("agent_type", "Coder")

    # 1. 查找空闲的同类型执行者
    if agent_type in executor_pool:
        for executor in executor_pool[agent_type]:
            if executor["status"] == "idle":
                executor["status"] = "busy"
                executor["task_id"] = task.id
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

    return executor_name
```

### 5. 调用 Agent 或创建 Team

**单任务**：
```
Agent(
    subagent_type=agent_type,
    prompt=task.description,
    background=True,
    context={"working_directory": os.getcwd()}
)
```

**多任务（Team）**：
```
TeamCreate(team_name="task-execution")

for task in parallel_tasks:
    executor_name = assign_task(task)
    Agent(
        subagent_type=agent_type,
        name=executor_name,
        team_name="task-execution",
        prompt=task.description,
        background=True
    )
```

### 6. 任务完成后清理

```
# 删除团队
TeamDelete()

# 清理空闲执行者
cleanup_idle_executors(max_idle_seconds=300)

def cleanup_idle_executors(max_idle_seconds):
    for agent_type, executors in list(executor_pool.items()):
        for executor in list(executors):
            if executor["status"] == "idle":
                idle_duration = datetime.now() - executor["idle_since"]
                if idle_duration > timedelta(seconds=max_idle_seconds):
                    tmux_session = f"task-exec-{agent_type.lower()}-{executor['name'].split('-')[-1]}"
                    subprocess.run(["tmux", "kill-session", "-t", tmux_session])
                    executors.remove(executor)
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

## Team 生命周期管理

### 1. Team 创建

当有多个任务需要并行执行时，创建 Team：

```
team_name = f"task-execution-{iteration}"
TeamCreate(team_name=team_name)
```

**创建时机**：
- 识别到 2 个或以上可并行任务
- 无依赖且文件无交集

### 2. 执行者分配

为每个任务分配执行者并加入 Team：

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
```

### 3. Team 执行监控

监控 Team 中所有执行者的状态：

```python
def monitor_team_progress(team_name):
    while True:
        teammates = TeamList()
        active_executors = [t for t in teammates if t.team_name == team_name]

        if not active_executors:
            break  # 所有执行者已完成

        # 更新任务进度
        for executor in active_executors:
            update_task_status(executor)

        # 输出进度
        print_progress_report()

        # 等待一段时间再检查
        time.sleep(5)
```

### 4. Team 清理

所有任务完成后，清理 Team：

```python
def cleanup_team(team_name):
    # 1. 等待所有执行者完成
    while True:
        teammates = TeamList()
        active_executors = [t for t in teammates if t.team_name == team_name]
        if not active_executors:
            break
        time.sleep(1)

    # 2. 删除 Team
    TeamDelete()

    # 3. 清理空闲执行者的 tmux session
    cleanup_idle_executors(max_idle_seconds=0)  # 立即清理

    print(f"[Team {team_name}] 已清理完成")
```

### 5. tmux Session 清理

精准清理执行者关联的 tmux session：

```python
def cleanup_executor_tmux(executor_name, agent_type):
    # 执行者名称格式：executor-{agent_type}-{index}
    # tmux session 名称格式：task-exec-{agent_type}-{index}

    index = executor_name.split('-')[-1]
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
```

### Team 生命周期规则

1. **创建**：仅在有多任务并行时创建
2. **执行**：步骤 3 内创建并执行
3. **清理**：步骤 3 结束时必须删除，步骤结束时必须无 Team 成员
4. **隔离**：每次迭代创建独立的 Team，不跨迭代复用
5. **验证**：清理后验证 Team 已删除，tmux session 已清理

## 并行规则

1. 每个并行任务至少有一个前置依赖（没有则父任务是前置依赖）
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

## 注意事项

- **工作目录一致性**：Agent 必须继承 leader 的 `os.getcwd()`
- **Team 生命周期**：参见"Team 生命周期管理"章节
- **资源清理**：精准清理执行者关联的 tmux session
- **不要跳过**：`tmux kill-server` 会清理所有 tmux，包括用户其他会话
- **执行者复用**：优先使用已存在的同类型空闲执行者
- **并行上限**：同时最多 2 个任务并行执行