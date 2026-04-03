# Task - 任务管理插件

> 基于 PDCA 循环的智能任务编排引擎，集成项目探索、计划设计、并行执行和质量递进的完整工作流

## 概述

Task 是一个任务管理框架插件，提供规划、执行、验证和迭代的完整流程。它不绑定任何具体的执行 agents，而是让用户灵活选择其他插件或自定义 agents 来完成实际工作。

**核心特性**：
- **MindFlow 执行引擎**：基于 PDCA 循环的 8 阶段持续迭代
- **项目探索体系**：8 个专业 Explorer Agents（通用/代码/前端/后端/数据库/API/测试/基础设施）
- **智能任务分解**：MECE 原则的原子任务拆分、DAG 依赖建模
- **质量递进机制**：60→75→85→90 分的深度迭代
- **统一用户交互**：Team Leader 模式集中管理调度和用户沟通

## 快速开始

```bash
/plugin install task@ccplugin-market
```

| 命令 | 说明 |
|------|------|
| `/loop [任务目标]` | 进入循环迭代模式，执行完整 PDCA 流程 |
| `/add [补充内容]` | 补充任务说明、纠正方向或添加约束 |
| `/cancel` | 取消当前执行，保留已完成工作 |

## MindFlow 8 阶段

| 阶段 | 说明 | 必须/可选 |
|------|------|----------|
| Initialization | 初始化状态、生成 task_id | 必须 |
| PromptOptimization | 任务边界分析+5W1H+prompt.md 持久化 | 必须 |
| DeepResearch | 收集最佳实践和技术方案 | 可选（复杂度>8） |
| Planning | MECE 分解任务、DAG 依赖、用户确认 | 必须 |
| Execution | 按计划调度 agent 执行任务 | 必须 |
| Verification | 验收标准检查（passed/failed） | 必须 |
| QualityGate | 质量评估（达标→Cleanup，不达标→PromptOptimization） | 必须 |
| Adjustment | 失败分析、升级策略（retry→debug→replan→ask_user） | 条件触发 |
| Cleanup | 资源清理、最终报告 | 必须 |

## 组件概览

- **Agents（14个）**：任务编排（planner/verifier）+ 项目探索（8个 explorer）+ 辅助（adjuster/finalizer/prompt-optimizer/execute）
- **Skills（15+）**：核心流程（loop/plan/verify）+ 探索（9个）+ 辅助（deep-iteration/memory-bridge/hooks 等）

## 详细文档

完整的组件索引、场景查找、常见问题和高级主题请参阅：

**[Task 插件完整导航索引](./NAVIGATION.md)**

## 许可证

AGPL-3.0-or-later
