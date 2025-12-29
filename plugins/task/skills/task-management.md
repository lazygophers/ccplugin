---
name: task-management
description: 任务管理系统 - 创建、跟踪、依赖管理。处理开发任务、项目规划时自动激活。
auto-activate:
  always: true
---

# 任务管理系统

## 快速开始

**自动初始化**：首次使用时，SessionStart hook 自动初始化工作空间（无需手动操作）

**推荐工作流**：
1. 需求规划 → 调用 task-planner agent
2. 任务拆解 → 调用 task-decomposer agent（对复杂任务）
3. 执行跟踪 → `task_ready`、`task_list`、`task_stats`
4. 导出文档 → `/task-export` command

## 核心工具优先级

**创建与查询**（高频）:
- `task_create` - 创建任务（必需：title）
- `task_list` - 列出任务（支持：status/priority/type 过滤，brief 模式节省 token）
- `task_ready` - **优先使用**：查找可执行任务（无阻塞依赖）

**状态管理**（中频）:
- `task_update` - 更新任务（status/priority/assignee）
- `task_show` - 查看详情（含依赖关系）
- `task_stats` - 统计概览（按状态/类型/优先级）

**依赖管理**（低频）:
- `task_dep_add` - 添加依赖（blocks/related/parent-child）
- `task_dep_remove` - 移除依赖

## 工作流模式

**开始工作**: `task_ready` → 选任务 → `task_update status=in_progress`
**创建任务**: `task_create` → 设 priority/tags → （可选）`task_dep_add` 设依赖
**进度追踪**: `task_list status=in_progress` → `task_stats` 查看整体进度
**完成任务**: `task_update status=closed` 或 `task_close`

## 最佳实践

- **brief 模式**：大部分查询用 `brief=true`（默认），减少 token 消耗
- **优先级**：0=Critical, 1=High, 2=Medium(默认), 3=Low, 4=Backlog
- **依赖类型**：`blocks`（硬阻塞，影响 task_ready）> `related`（软关联）
- **状态流转**：open → in_progress → closed（或 blocked/deferred）
