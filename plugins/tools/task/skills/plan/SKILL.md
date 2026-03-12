---
name: plan
description: 计划设计规范 - 任务分解、依赖建模、agents/skills 分配的执行规范
user-invocable: false
context: fork
---

# 计划设计规范

计划设计是 loop 循环的第二步，负责将任务分解为原子子任务、建立依赖关系、分配 agents 和 skills。

## 执行目标

- 将主任务分解为原子性的子任务
- 建立子任务之间的依赖关系（DAG）
- 为每个子任务分配 agent 和 skills
- 确保任务可并行执行且无文件冲突

## 执行步骤

### 1. 任务分解

使用工具：TaskCreate

分解策略：
- **按功能分解**：新功能 → 数据层 + 逻辑层 + 接口层 + 测试
- **按阶段分解**：迁移 → 准备 → 核心迁移 → 适配 → 验证 → 清理
- **按文件分解**：变更 → 文件A修改 + 文件B修改 + 文件C新建 + 测试更新

分解原则：
- 每个子任务只做一件事（单一职责）
- 每个子任务必须是原子性的、不可再分的
- 每个子任务有明确的输入和输出
- 任务粒度：可在一次执行周期完成

调用示例：
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

### 2. 建立依赖关系

使用工具：TaskUpdate

依赖类型：
- **数据依赖**：B 需要 A 的输出作为输入
- **顺序依赖**：B 必须在 A 之后执行
- **资源依赖**：A 和 B 操作同一文件，不能并行

建立依赖：
```
TaskUpdate(
  task_id=task_b_id,
  addBlockedBy=[task_a_id]
)
```

依赖规范：
- 确认依赖图无环（DAG）
- 识别可并行任务（无依赖、不操作同一文件）
- 并行任务数不超过 2

### 3. 分配 agents 和 skills

为每个任务指定：
- **agent_type**：执行该任务的 agent 类型（如 coder、tester、researcher）
- **skills**：该任务需要的 skills 列表（如 python:core、golang:error）

Agent 来源：
- 其他插件提供的 agents（如 golang、python、flutter 插件）
- 用户或项目自定义的 agents
- 通用 agents（如 general-purpose、Explore）

Skills 来源：
- 其他插件提供的 skills
- 用户或项目自定义的 skills

### 4. 调用 Agent 进行规划

使用工具：Agent

如果任务复杂需要辅助规划：
```
import os

Agent(
  subagent_type="planner",  # 使用规划类 agent
  task="分析任务复杂度并建议分解方案",
  background=True,  # 尽可能使用后台运行
  context={
    "main_task": "...",
    "collected_info": "...",
    "working_directory": os.getcwd()  # 继承 leader 的工作目录
  }
)
```

**执行要求**：
- 所有 agent 尽可能使用 `background=True` 在后台运行
- Agent 的工作目录必须与 leader 完全一致（通过 `working_directory` 传递）
- 后台运行可以提升执行效率，减少主线程阻塞

Agent 通过 SendMessage 上报规划建议给 leader。

## 并行执行规划

### 并行条件

两个任务可以并行执行当且仅当：
1. 无依赖关系
2. 不修改同一文件（通过 target_files 检查）
3. 不修改同一模块或包
4. 总并行数不超过 2

### 动态队列规划示例

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

**规划原则**：
- 无依赖任务可并行（T1, T2）
- 依赖满足后自动启动（T1完成→T3启动）
- 队列动态调度，保持最多 2 个并行

## 验收标准定义

每个任务必须定义可自动验证的验收标准：

格式：
```
验收标准：
- [ ] 可自动验证的检查项 1
- [ ] 可自动验证的检查项 2
- [ ] 可自动验证的检查项 3
```

要求：
- 必须可自动验证（测试通过、编译成功、lint 无错误）
- 避免主观判断（如"代码质量好"）
- 每项独立可检查
- 优先级：运行测试 > 检查输出 > 人工确认

## 输出要求

计划设计完成后：
1. 所有子任务已通过 TaskCreate 注册
2. 依赖关系已通过 TaskUpdate 建立
3. 每个任务的 metadata 包含 target_files、agent_type、skills
4. 任务状态初始化为 pending
5. 不将计划写入文件（TaskList 是唯一状态来源）

## 注意事项

- 不要过度分解简单任务
- 不要假设 agent 名称，使用项目实际可用的 agents
- 确保并行任务的 target_files 无交集
- Agent 遇到问题通过 SendMessage 上报给 leader
