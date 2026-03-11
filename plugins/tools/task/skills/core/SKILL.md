---
name: core
description: 任务管理核心规范 - 任务生命周期、状态机、角色分工和基本原则。所有任务管理操作前必须加载。
user-invocable: true
context: fork
---

# 任务管理核心规范

## 任务生命周期

```
创建 → 规划 → 确认 → 执行 → 验收 → 完成
                         ↑        |
                         └─ 修复 ←┘
```

## 任务状态机

| 状态 | 说明 | 可转换到 |
|------|------|---------|
| `pending` | 待执行 | `in_progress`, `cancelled` |
| `in_progress` | 执行中 | `completed`, `failed`, `blocked` |
| `completed` | 已完成 | `in_review` |
| `failed` | 执行失败 | `in_progress`(重试), `cancelled` |
| `blocked` | 被阻塞 | `in_progress`(解除阻塞) |
| `in_review` | 审查中 | `completed`, `in_progress`(需修复) |
| `cancelled` | 已取消 | - |

## 角色分工

| 角色 | 职责 | 介入时机 |
|------|------|---------|
| **planner** | 任务分解、依赖分析 | 任务创建时 |
| **executor** | 具体执行和自验证 | 任务执行时 |
| **reviewer** | 质量审查和验收 | 任务完成后 |
| **orchestrator** | 调度和编排 | 多任务协调时 |
| **debugger** | 问题诊断和修复 | 任务失败时 |

## 核心原则

### 1. 规划先行
- 非平凡任务必须先规划后执行
- 规划结果需要用户确认后才执行
- 过于简单的任务（<3分钟）可直接执行

### 2. 单一职责
- 每个子任务只做一件事
- 每个子任务有明确的输入和输出
- 子任务之间通过输入输出连接

### 3. 验证驱动
- 每个子任务必须有可自动验证的验收标准
- 完成后立即验证，不积压
- 验收标准的优先级：运行测试 > 检查输出 > 人工确认

### 4. 最小并行
- 并行任务数不超过 2
- 并行任务不得操作同一文件
- 等待并行组完成后再进入下一组

### 5. 快速失败与升级
- 失败时立即报告，不静默继续
- 遵循升级链：executor 重试 → debugger 诊断 → reviewer/planner 重新规划 → 用户指导
- 连续无进展时中断并请求用户指导

### 6. 提问规范
- **Agent 不得直接向用户提问**
- Agent 遇到需要用户决策的问题时，将问题上报给 Team 管理者（orchestrator）
- 由 Team 管理者通过 `AskUserQuestion` 工具统一向用户提问
- 问题必须包含充足的上下文、可选方案和建议方向

## 任务状态管理

所有任务状态通过内置的 `TaskCreate` / `TaskUpdate` / `TaskGet` / `TaskList` 系统管理，**不写入文件**。

**状态来源**：TaskList/TaskGet 是任务状态的唯一真实来源。

**清理规范**：所有子任务完成并通过审查后，清理 TaskList 中已完成的任务条目。

## 内置工具使用规范

### 什么时候用什么工具

**规划完成后** — 使用 `TaskCreate` 为每个子任务创建条目，使用 `TaskUpdate` 设置 `addBlockedBy` 建立任务间的依赖关系

**需要多 Agent 并行执行时** — 使用 `TeamCreate` 创建团队，使用 `Agent`（带 `team_name` 和 `name`）生成团队成员

**分配任务时** — 使用 `TaskUpdate` 设置 `owner` 将任务分配给成员，同时设置 `status` 为 `in_progress`

**查看进度时** — 使用 `TaskList` 查看所有任务状态，使用 `TaskGet` 获取某个任务的详细信息和依赖

**团队内通信时** — 使用 `SendMessage` 给指定成员发消息（分配任务、指导修复、协调工作）

**需要全员通知时** — 使用 `SendMessage` 的 broadcast 模式，仅用于紧急阻塞性问题

**需要向用户提问时** — 使用 `AskUserQuestion` 统一提问，只有 orchestrator 有权使用

**任务完成关闭团队时** — 使用 `SendMessage` 的 shutdown_request 逐个关闭成员，全部关闭后使用 `TeamDelete` 清理

**需要终止后台任务时** — 使用 `TaskStop` 终止，使用 `TaskOutput` 获取已有输出

### 任务元数据

每个任务通过 `TaskUpdate` 的 `metadata` 附加以下信息：
- `target_files`：该任务操作的文件列表（用于并行隔离检查）
- `retry_count`：重试次数（用于三次失败升级）
- `failure_reason`：最近一次失败原因

### 并行执行约束
- **最大并行数：2** — 超过时排队等待
- **文件隔离** — 并行任务不得修改同一文件（通过 metadata.target_files 检查）
- **包隔离** — 并行任务不得修改同一包
- 分配任务前必须检查 target_files 无交集

## 子任务定义模板

```markdown
### T[N]: [标题]
- **描述**：[做什么、为什么做]
- **输入**：[文件/数据/前置任务输出]
- **输出**：[文件变更/数据产出]
- **依赖**：[T1, T2] 或 无
- **验收标准**：
  - [ ] [可自动验证的条件]
- **执行方式**：Agent/直接执行
```
