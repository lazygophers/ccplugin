# Task - 任务管理插件

> 基于状态机的任务编排引擎，集成探索、对齐、规划、执行、验证和调整的完整工作流

## 概述

Task 是一个任务管理框架插件，提供从需求对齐到执行验收的完整流程。通过 8 个状态的有序流转，实现任务的自动化编排和质量保障。

**核心特性**：
- **状态机驱动**：8 状态流转（pending→explore→align→plan→exec→verify→adjust→done）
- **DAG 执行引擎**：基于依赖关系的子任务调度，2 worker 协程并发
- **SMART-V 验收**：验收标准遵循 Specific/Measurable/Achievable/Relevant/Time-bound/Verifiable 原则
- **自我迭代**：verify→adjust 循环，自动分析失败原因并修正

## 快速开始

```bash
/plugin install task@ccplugin-market
```

## 状态流转

| 状态 | 说明 | 触发条件 |
|------|------|----------|
| pending | 等待调度 | 任务创建 |
| explore | 现状探索 | 上下文缺失 |
| align | 范围对齐 | 与用户确认目标、验收标准、边界 |
| plan | 任务规划 | 分解为 DAG 子任务 |
| exec | 任务执行 | 按 DAG 调度执行 |
| verify | 结果校验 | 对照验收标准检查 |
| adjust | 调整修正 | 校验失败时分析原因 |
| done | 完成 | 唯一终态 |

## 组件概览

**Agents（5 个）**：
- `explore` — 现状探索，收集上下文
- `plan` — 任务分解，制定执行方案
- `verify` — 结果校验
- `adjust` — 失败分析与修正策略
- `done` — 任务终结与资源清理

**Skills（9 个）**：
- `flow` — 状态机调度器，协调全流程
- `resume` — 恢复中断的任务，从断点继续
- `align` / `explore` / `plan` / `exec` / `verify` / `adjust` / `done` — 各阶段核心逻辑

## 详细文档

- **[状态管理](./docs/状态管理.md)** — 状态定义、转换规则、状态图
- **[输出格式](./docs/output-format.md)** — `[flow·{task_id}·{state}]` 前缀规范
- **[数据格式](./docs/metadata.md)** — index.json 任务索引文件格式

## 许可证

AGPL-3.0-or-later
