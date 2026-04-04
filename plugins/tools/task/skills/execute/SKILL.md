---
description: "Execute 任务执行 - Loop Execution 阶段调用：按依赖顺序调度子任务，支持最多2个任务并行（Agent run_in_background），跟踪执行进度和结果收集。由 Loop 内部调度，不直接面向用户"
model: sonnet
user-invocable: false
hooks:
  SessionStop:
    - hooks:
        - type: command
          command: "PLUGIN_NAME=task uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks_skills"
  SubagentStart:
    - hooks:
        - type: command
          command: "PLUGIN_NAME=task uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks_skills"
---


# Skills(task:execute) - 任务执行规范

<overview>

本规范定义了 Loop 命令中任务执行（Execution / Do）阶段的行为。该阶段负责将计划设计阶段产出的子任务按依赖顺序调度执行，支持最多 2 个任务并行。

单任务场景直接调用 Agent 即可，多任务场景使用 `Agent(..., run_in_background=True)` 并行执行（最多 2 个）。

</overview>

<red_flags>

| AI Rationalization | Reality Check |
|-------------------|---------------|
| "三个任务都可以并行" | 并行度硬性限制<=2，第三个任务必须等第一批完成 |
| "这些任务没有文件冲突，可以并行执行" | 文件无交集只是必要非充分条件，还需检查依赖关系 |
| "监控进度时可以跳过进度报告，直接等完成" | 进度报告是实时性要求，必须定期输出 |
| "工作目录用默认值就行" | 必须显式传递 working_directory 确保一致 |

</red_flags>

<execution_flow>

## 执行流程

### 1. 获取待执行任务

从 TaskList 获取 pending 状态的任务。

### 2. 检查依赖并识别可并行任务

检查每个任务的 dependencies 是否已满足，识别无依赖且文件无交集的任务作为可并行候选。

### 3. 单任务执行

```python
Agent(
    agent=task.metadata.get("agent", "coder"),
    prompt=task.description,
    run_in_background=False
)
```

### 4. 多任务并行执行

使用 Agent 的 `run_in_background=True` 参数并行执行（最多 2 个）：

```python
for task in parallel_batch[:2]:
    Agent(
        agent=task.metadata.get("agent", "coder"),
        prompt=task.description,
        run_in_background=True
    )
# 等待所有后台 Agent 完成，收集结果
```

### 5. 监控与进度报告

实时追踪执行状态，记录每个任务的开始/结束时间，捕获结果和错误。

</execution_flow>

<output_format>

## 输出格式

执行过程中实时输出任务进度：

```
[MindFlow·${任务内容}·任务执行/${迭代轮数}·running]
任务进度：
T1: 创建用户模型 ········ 已完成
T2: 创建订单模型 ········ 进行中
T3: 创建商品模型 ········ 待执行(依赖 T2)
```

</output_format>

<rules>

## 并行规则

- 同时最多 2 个槽位执行任务
- 依赖已满足的任务可以被调度
- 槽位释放时立即检查队列，启动下一个 Ready 任务
- 任务完成后重新评估所有 Blocked 任务的依赖状态

## 必须遵守的约束

**工作目录一致性**：Agent 必须继承 leader 的 os.getcwd()，通过 context 传递 working_directory。

**任务创建规范**：TaskCreate 时必须在 metadata 中指定 agent，例如 `TaskCreate(..., metadata={"agent": "coder", "skills": [...]})`。

**禁止使用 TeamCreate/TeamDelete**：所有任务执行通过 Agent 直接调用或 `Agent(..., run_in_background=True)` 并行执行。Agent 自动管理资源生命周期，无需手动清理。

</rules>

