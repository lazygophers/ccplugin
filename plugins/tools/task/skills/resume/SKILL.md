---
description: 恢复中断任务。当用户要求继续、恢复之前未完成的任务时触发，读取 index.json 检查数据完整性，确定恢复点后调用 flow 继续执行
memory: project
color: purple
permissionMode: bypassPermissions
background: false
user-invocable: true
effort: low
context: none
disable-model-invocation: true
argument-hint: [task_id（可选）]
---

# Resume Skill

恢复因会话中断（关闭终端、网络断开、/clear 等）而未完成的任务。

## 工作原理

任务插件在每次状态转换时自动将当前状态写入 `index.json`。数据文件（context.json、align.json、task.json）作为天然检查点保留在磁盘上。Resume 读取这些持久化状态，确定中断点，然后将 flow 定位到正确位置继续。

> 文件级变更的回滚由 Claude Code 内置的 `/rewind` 处理，本 skill 不重复此功能。

## 执行流程

### 步骤 1：读取任务索引

读取 `.lazygophers/tasks/index.json`。如果索引为空或不存在，输出"没有找到任何任务记录"并结束。

### 步骤 2：筛选未完成任务

从索引中筛选状态不是 done / cancel 的任务。如果没有未完成任务，输出"没有需要恢复的任务"并结束。

### 步骤 3：选择恢复目标

- 如果用户指定了 task_id（通过 $ARGUMENTS）→ 直接恢复该任务
- 否则 → 通过 AskUserQuestion 展示未完成任务列表，让用户选择

### 步骤 4：快速恢复检查

如果 `.lazygophers/tasks/{task_id}/.state.json` 存在，读取它获取上次状态快照（current_state、transition_count）。这是快速路径，但仍需验证数据文件完整性。

### 步骤 5：数据文件完整性验证

逐个检查数据文件，验证文件存在且包含必需字段。文件损坏或字段缺失时视为不存在，降级到更早的恢复点。

| 文件 | 必需字段 |
|------|---------|
| context.json | task_related, code_style |
| align.json | task_goal, acceptance_criteria |
| task.json | subtasks |

如果 task.json 存在且包含 checkpoint 字段，读取检查点获取更精确的恢复信息（已完成/已失败的子任务列表）。

### 步骤 6：确定恢复状态

根据中断时的状态和数据文件完整性，确定 flow 应从哪个状态开始：

| 条件 | 恢复到 |
|------|--------|
| 中断在 pending/explore，或 context.json 缺失/损坏 | explore |
| 中断在 align，或 align.json 缺失/损坏 | align |
| 中断在 plan，或 task.json 缺失/损坏 | plan |
| 中断在 exec，有 checkpoint 且全部完成 | verify |
| 中断在 exec，其他情况 | exec（DAG 跳过已完成的子任务） |
| 中断在 verify/adjust | verify |
| 其他 | align（兜底） |

### 步骤 7：构建恢复上下文摘要

从已有数据文件中提取关键信息，传给 flow 避免 agent 重新探索：

- 从 context.json：modules、toolchain
- 从 align.json：goal、criteria_count
- 从 checkpoint：completed_subtasks、failed_subtasks

### 步骤 8：调用 flow

调用 `Skill("task:flow")`，传入 task_id、resume_from（恢复状态）和 resume_context（上下文摘要）。

## 检查清单

- [ ] index.json 已读取
- [ ] 未完成任务已筛选
- [ ] 用户已选择/指定恢复目标
- [ ] 数据文件完整性已验证（存在性 + 必需字段）
- [ ] 损坏/不完整的文件已降级处理
- [ ] 恢复状态已确定
- [ ] 恢复上下文已构建
- [ ] flow skill 已调用
