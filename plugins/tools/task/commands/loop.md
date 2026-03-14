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

这是一个全新任务，你需要完成

<user_task>
$ARGUMENTS
</user_task>

作为 team leader，负责调度所有工作，持续迭代直到任务目标达成。

## ⚠️ 必须遵守的约束

1. **并行上限**：最多 2 个任务同时执行
2. **工作目录一致性**：Agent 必须继承 leader 的 `os.getcwd()`
   - 通过 `context` 传递 `working_directory: os.getcwd()`
   - 使用 tmux 时：`tmux new-session -d -s agent -c $(pwd)`
3. **Team 生命周期**：步骤 4 创建 team，步骤 4 结束时删除执行完成后清理
4. **提问权限**：只有 leader 可调用 AskUserQuestion
5. **验收标准**：必须量化（测试覆盖率、性能指标等）
6. **执行顺序**：严格按 6 步循环（信息收集→计划设计→确认→执行→验证→调整）
7. **任务创建规范**：TaskCreate 时必须在 metadata 中指定 agent_type
   - 示例：`TaskCreate(..., metadata={"agent_type": "Coder", "skills": [...]})`
   - 目的：明确任务由哪个类型的 agent 执行，便于执行者复用和调度
8. **执行者复用**：尽可能复用已创建的执行者，避免重复创建
   - 优先使用已存在且空闲的 executor（同 agent_type）
   - 仅在无可复用执行者或所有执行者忙碌时创建新的
   - 通过 executor 名称标识和管理（如 `executor-coder-1`, `executor-tester-1`）
   - **及时清理不需要的执行者**：当某类型执行者长时间空闲或不再需要时，主动清理
9. **资源清理**：精准清理执行者关联的资源，避免资源泄漏
   - **清理执行者关联的 tmux session**（不是清理所有 tmux）
   - 通过执行者名称匹配对应的 tmux session（如 `executor-coder-1` → tmux session `task-exec-coder-1`）
   - 清理时机：执行者不再需要时（长时间空闲、步骤 4 结束、Loop 完成）
   - 验证资源释放：确认特定 tmux session 已删除（`tmux ls | grep <session-pattern>`）
10. **[Looping] 前缀规范**：Loop 执行过程中所有输出必须带前缀
   - 格式：`[Looping | 第{N}轮 | 步骤{X}: {步骤名}]`
   - 示例：`[Looping | 第1轮 | 步骤1: 信息收集]`、`[Looping | 第2轮 | 步骤4: 任务执行]`
   - 包含信息：当前迭代次数、当前步骤编号和名称
   - 自动移除：loop 完成或退出时不再输出前缀
   - 目的：让用户清晰追踪 loop 执行状态和进度

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

**Agents 不直接提问**：所有 agents 不得直接调用 AskUserQuestion。

## 执行流程

### 初始化

循环开始时执行一次：

```
# 1. 创建主任务
TaskCreate(
  title="Loop 主任务",
  description=用户提供的任务目标,
  acceptance_criteria=[...]
)

# 2. 初始化状态
iteration = 0
stalled_count = 0
max_stalled_attempts = 3
team_id = None  # 团队 ID，仅在需要时创建
```

### 步骤 1：信息收集

**目标**：收集足够的项目信息以支持任务规划。

**详细规范**：参见 Skills(task:gather)

**输出示例**：`[Looping | 第1轮 | 步骤1: 信息收集] 开始收集项目信息...`

**要点**：

- 使用 Read/Glob/Grep 读取项目文件、文档、CLAUDE.md
- 使用 Agent(Explore) 深度分析代码结构
- 通过 AskUserQuestion 确认不确定部分
- 收集：目标、约束、上下文、文件路径、测试覆盖

### 步骤 2：计划设计

**目标**：将任务分解为原子子任务，建立依赖关系。

**详细规范**：参见 Skills(task:plan)

**输出示例**：`[Looping | 第1轮 | 步骤2: 计划设计] 开始任务分解，识别依赖关系...`

**核心原则**：MECE、可交付原子化、可量化可验证、依赖闭环

**避坑**：禁止过度拆分、权责模糊、完成标准模糊

**输出**：所有子任务已注册（TaskCreate），依赖已建立（TaskUpdate addBlockedBy）。

### 步骤 3：计划确认

**目标**：向用户展示计划并获得确认（使用 AskUserQuestion）。

**输出示例**：`[Looping | 第1轮 | 步骤3: 计划确认] 请确认以下执行计划...`

**输出格式**（必填项：执行流程图（含每个任务 agent/skills/files）、量化验收标准、简要说明）：

```markdown
## 执行计划

### 执行流程图（任务队列 + 两槽位并行模型）
┌───────────────────────────────────────────────────────────────┐
│ T1: 数据库迁移                                                 │
│ agent : devops                                                │
│ skills: sql, migration                                        │
│ files : migrations/001_init.sql                               │
└───────────────────────────────┬───────────────────────────────┘
│
┌───────────┬───────────┼───────────┬───────────┐
│           │           │           │           │
▼           ▼           ▼           ▼           ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ T2: 用户模型 │ │ T3: 订单模型 │ │ T4: 商品模型 │ │ T5: 库存模型 │ │ T6: 通知模块 │
│ agent: coder│ │ agent: coder│ │ agent: coder│ │ agent: coder│ │ agent: coder│
│ skills:     │ │ skills:     │ │ skills:     │ │ skills:     │ │ skills:     │
│ python:core │ │ python:core │ │ python:core │ │ python:core │ │ python:core │
│ files:      │ │ files:      │ │ files:      │ │ files:      │ │ files:      │
│ user.py     │ │ order.py    │ │ product.py  │ │ inventory.py│ │ notify.py   │
│ (依赖 T1)   │ │ (依赖 T1)   │ │ (依赖 T1)   │ │ (依赖 T1)   │ │ (依赖 T1)   │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
│               │               │               │               │
▼               │               └──────┬──────────┘               │
┌─────────────┐        │                      ▼                           │
│ T7: 支付模块│        │         ┌───────────┬───────────┐               │
│ agent: coder│        │         │           │           │               │
│ skills:     │        │         ▼           ▼           ▼               │
│ python:core │        │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ payment     │        │ │ T8: 价格计算 │ │ T9: 商品搜索 │ │ T10:商品分类 │ │
│ files:      │        │ │ agent: coder│ │ agent: coder│ │ agent: coder│ │
│ payment.py  │        │ │ skills:     │ │ skills:     │ │ skills:     │ │
│ (依赖 T2)   │        │ │ python:core │ │ python:core │ │ python:core │ │
└──────┬──────┘        │ │ files:      │ │ files:      │ │ files:      │ │
│               │ │ pricing.py  │ │ search.py   │ │ category.py │ │
│               │ │ (依赖 T4)   │ │ (依赖 T4)   │ │ (依赖 T4)   │ │
│               │ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ │
│               │        │               │               │        │
└───────────────┴────────┴───────────────┴───────────────┴────────┘
│
▼
┌───────────────────────────────────┐
│ T11: 集成测试                      │
│ agent : tester                    │
│ skills: python:testing            │
│ files : tests/test_integration.py │
│ (依赖 T3, T5-T10)                  │
└───────────────────────────────────┘

**任务队列 + 槽位执行时间线**（最多 2 个并行）：
┌─────────────────────────────────────────────┐
│              任务队列                        │
│  [依赖已满足的 Ready 任务]                    │
└───────────────┬─────────────────────────────┘
      从队列取出，填充空闲槽位
	┌──────────────┴─────────┐
	│                        │
	▼                        ▼
	┌──────────┐        ┌──────────┐
	│ Slot #1  │        │ Slot #2  │
	└──────────┘        └──────────┘

时刻 0:
Queue: [T1✓]
Slot#1: T1 启动
Slot#2: 空闲

时刻 1: (T1 完成)
Queue: [T2✓, T3✓, T4✓, T5✓, T6✓] ← T2-T6 依赖满足
Slot#1: 空闲 → T2 启动 (自动补位)
Slot#2: 空闲 → T3 启动 (自动补位)

时刻 2: (T2 完成)
Queue: [T4✓, T5✓, T6✓, T7✓] ← T7 依赖满足
Slot#1: 空闲 → T4 启动 (自动补位)
Slot#2: T3 运行中

时刻 3: (T3 完成, T4 完成)
Queue: [T5✓, T6✓, T7✓, T8✓, T9✓, T10✓] ← T8-T10 依赖满足
Slot#1: 空闲 → T5 启动 (自动补位)
Slot#2: 空闲 → T6 启动 (自动补位)

时刻 4: (T5 完成, T6 完成)
Queue: [T7✓, T8✓, T9✓, T10✓]
Slot#1: 空闲 → T7 启动 (自动补位)
Slot#2: 空闲 → T8 启动 (自动补位)

时刻 5: (T7 完成, T8 完成)
Queue: [T9✓, T10✓]
Slot#1: 空闲 → T9 启动 (自动补位)
Slot#2: 空闲 → T10 启动 (自动补位)

时刻 6: (T9 完成, T10 完成)
Queue: [T11✓] ← T11 依赖满足
Slot#1: 空闲 → T11 启动 (自动补位)
Slot#2: 空闲

时刻 7: (T11 完成)
Queue: []
→ 全部完成 ✓

**执行逻辑**：

- ✓ 表示依赖已满足（Ready）
- 槽位释放时立即检查队列，自动启动下一个 Ready 任务
- 任务完成后重新评估所有 Blocked 任务的依赖状态
- 始终保持最多 2 个任务并行执行

### 验收标准（必须量化）

- [ ] 单元测试覆盖率 ≥ 90%
- [ ] 所有 CI 检查通过（lint/test/build）
- [ ] 验收标准与需求 1:1 映射
- [ ] 无新增技术债（代码复杂度 ≤ X）
- [ ] 无影响已有功能（回归测试通过）

### 简要说明（≤100字）

[任务概述和执行策略]
```

**确认**：用户确认后继续，不确认则回到步骤 2 调整。

### 步骤 4：任务执行

**目标**：按依赖顺序调度执行所有子任务。

**详细规范**：参见 Skills(task:execute)

**输出示例**：
- 开始执行：`[Looping | 第1轮 | 步骤4: 任务执行] 开始调度任务...`
- 进度更新：`[Looping | 第1轮 | 步骤4: 任务执行] T1 完成，启动 T2 和 T3（并行）...`
- 执行者复用：`[Looping | 第1轮 | 步骤4: 任务执行] 复用执行者 executor-coder-1...`

**核心流程**：

1. TaskList 获取待执行任务
2. 判断任务数量：1个任务直接调用 Agent，多个任务创建 team
3. TaskGet 检查依赖，识别可并行任务（无依赖+文件无交集）
4. **执行者复用机制**（优先复用已存在的执行者）：
   - 维护执行者池：`executor_pool = {agent_type: [executor_name, ...]}`
   - 分配任务前检查：是否有相同 `agent_type` 的空闲执行者
   - 复用策略：
     - ✅ 优先使用已存在且空闲的同类型执行者
     - ✅ 仅在无可复用执行者或槽位已满时创建新的
     - ✅ 通过命名规范管理：`executor-{agent_type}-{序号}`（如 `executor-coder-1`）
   - 状态跟踪：记录每个执行者的任务分配和完成状态
5. Agent 调用（background=True，传递 working_directory）
6. 最多 2 个任务并行，TaskUpdate 更新状态
7. 处理 SendMessage（agent 上报）
8. **执行完成后清理**：
   - TeamDelete 删除团队（如果创建了 team）
   - **精准清理执行者关联的 tmux session**（⚠️ 不清理所有 tmux）：
     - 通过执行者名称定位对应的 tmux session
     - 示例：执行者 `executor-coder-1` → tmux session `task-exec-coder-1`
     - 清理命令：`tmux kill-session -t task-exec-coder-1`（仅清理特定 session）
     - ❌ 错误：`tmux kill-server`（会清理所有 tmux，包括用户其他会话）
   - 及时清理不需要的执行者：
     - 长时间空闲的执行者（如 5 分钟无新任务）
     - 特定类型任务全部完成后的执行者
   - 验证资源释放：
     - 确认特定 tmux session 已删除：`tmux ls | grep task-exec-coder-1`
     - 确认无残留执行者进程

**⚠️ Team 生命周期**：本步骤内创建和删除，步骤结束时必须无Team成员。

**执行者复用示例**：

```python
# 初始化执行者池
executor_pool = {}  # {agent_type: [{name: executor-xxx, status: idle/busy, task_id: ...}]}

# 分配任务
def assign_task_to_executor(task):
    agent_type = task.metadata.get("agent_type", "Coder")

    # 1. 查找空闲的同类型执行者
    if agent_type in executor_pool:
        for executor in executor_pool[agent_type]:
            if executor["status"] == "idle":
                # 复用已有执行者
                executor["status"] = "busy"
                executor["task_id"] = task.id
                print(f"[复用] 执行者 {executor['name']} 分配任务 {task.id}")
                return executor["name"]

    # 2. 无可复用执行者，创建新的
    if agent_type not in executor_pool:
        executor_pool[agent_type] = []

    executor_index = len(executor_pool[agent_type]) + 1
    executor_name = f"executor-{agent_type.lower()}-{executor_index}"

    executor_pool[agent_type].append({
        "name": executor_name,
        "status": "busy",
        "task_id": task.id
    })

    print(f"[新建] 执行者 {executor_name} 分配任务 {task.id}")
    return executor_name

# 任务完成后释放执行者
def release_executor(executor_name):
    for agent_type, executors in executor_pool.items():
        for executor in executors:
            if executor["name"] == executor_name:
                executor["status"] = "idle"
                executor["task_id"] = None
                executor["idle_since"] = datetime.now()
                print(f"[释放] 执行者 {executor_name} 已空闲")
                return

# 清理不需要的执行者（定期调用或步骤 4 结束时调用）
def cleanup_idle_executors(max_idle_seconds=300):
    import subprocess
    from datetime import datetime, timedelta

    for agent_type, executors in list(executor_pool.items()):
        for executor in list(executors):
            # 检查空闲时间
            if executor["status"] == "idle" and "idle_since" in executor:
                idle_duration = datetime.now() - executor["idle_since"]
                if idle_duration > timedelta(seconds=max_idle_seconds):
                    # 清理执行者关联的 tmux session
                    tmux_session = f"task-exec-{agent_type.lower()}-{executor['name'].split('-')[-1]}"
                    try:
                        subprocess.run(
                            ["tmux", "kill-session", "-t", tmux_session],
                            capture_output=True,
                            check=False  # 不抛出异常，session 可能已不存在
                        )
                        print(f"[清理] tmux session {tmux_session} 已删除")
                    except Exception as e:
                        print(f"[清理] tmux session {tmux_session} 清理失败: {e}")

                    # 从执行者池移除
                    executors.remove(executor)
                    print(f"[清理] 执行者 {executor['name']} 已移除（空闲 {idle_duration.total_seconds():.0f}s）")

        # 如果该类型执行者全部清理，移除该类型
        if not executors:
            del executor_pool[agent_type]
```

### 步骤 5：结果验证

**前置条件**：✓ Team已删除（由步骤4完成）

**目标**：验证所有任务的验收标准是否通过。

**详细规范**：参见 Skills(task:verify)

**输出示例**：`[Looping | 第1轮 | 步骤5: 结果验证] 开始验证所有验收标准...`

**执行流程**：

1. TaskList, TaskGet 检查所有任务
2. 验证每个任务的验收标准（运行测试、检查输出、验证文件）
3. 验证无影响已有功能和别的模块（回归测试）
4. TaskUpdate 记录验证结果

**判断**：

- 验收失败 → 步骤 6
- 验收通过 + 有建议 → AskUserQuestion 询问是否属于任务范围
- 验收通过 + 无建议 → Loop 完成，跳到清理阶段

### 步骤 6：失败调整

**目标**：分析失败原因，决定下一步策略，回到步骤 2 重新规划。

**输出示例**：`[Looping | 第2轮 | 步骤6: 失败调整] 分析失败原因，准备重新规划...`

**执行流程**：

1. 分析失败原因（错误分类：编译/测试/依赖/其他）
2. 检测停滞（相同错误重复 → stalled_count++）
3. 应用失败升级策略
4. 回到步骤 2

**失败升级策略**：

- 第 1 次失败：调整后重试
- 第 2 次失败：调试 Agent 诊断
- 第 3 次失败：重新规划任务
- 停滞 3 次：AskUserQuestion 请求用户指导（重置 stalled_count，继续循环）

### 清理阶段

Loop 完成时执行一次，输出最终报告：

**注意**：此阶段不再使用 `[Looping]` 前缀，直接输出报告。

```
=== Loop 完成 ===
状态：成功（所有验收标准通过）
总迭代次数：N | 变更文件：[列表] | 停滞次数：M | 用户指导次数：K
Team 清理：已在步骤 4 完成
前缀状态：已移除（loop 已退出）
```

## 终止条件

- **目标达成**：步骤 5 全部通过 → 正常退出，输出报告
- **停滞过多**：连续 3 次相同错误 → 请求用户指导后继续（不退出）
- **用户中断**：用户主动中断 → 根据指令处理

**重要**：无最大迭代次数限制，停滞时继续循环。

## 执行原则

严格遵守顶部"⚠️ 必须遵守的约束"，此外：

- 不要跳过计划确认步骤
- Agents 通过 SendMessage 上报问题
- 停滞时请求用户指导，但继续循环（不退出）