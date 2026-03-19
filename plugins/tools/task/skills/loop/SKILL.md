---
description: Loop 持续执行 - 作为 team leader 执行完整的任务管理循环，包括计划设计、执行、验证、调整
argument-hint: [ 任务目标描述 ]
skills:
  - task:planner
  - task:execute
  - task:verifier
  - task:adjuster
  - task:loop-planning
  - task:loop-verification
  - deepresearch:deep-research
model: sonnet
memory: project
---

# MindFlow - 迭代式任务编排引擎

<overview>

基于 PDCA 循环的智能任务编排引擎。核心职责：通过持续迭代完成复杂任务，确保质量和可靠性。

**关键特性**：
- **深度迭代**：质量递进（60→75→85→90分），最小迭代次数基于复杂度
- **状态机**：9状态完整生命周期（初始化→深度研究→计划设计→计划确认→任务执行→结果验证→质量门控→失败调整→全部完成）
- **Team Leader**：统一用户交互，调度 4 个核心 agent（planner、executor、verifier、adjuster）

</overview>

<execution>

## PDCA 执行流程

执行 PDCA 循环：**Plan**（task:loop-planning）→ **Do**（task:execute）→ **Check**（task:loop-verification）→ **Act**（task:adjuster）

### 核心阶段

1. **初始化**：初始化状态变量、深度迭代配置
2. **深度研究**（可选）：第1轮、失败2次、质量不达标、复杂任务时触发
3. **计划设计**：调用 task:loop-planning 生成执行计划
4. **任务执行**：调用 task:execute 并行执行（最多2个）
5. **结果验证**：调用 task:loop-verification 验证质量
6. **失败调整**：调用 task:adjuster 应用升级策略（retry→debug→replan→ask_user）
7. **全部完成**：清理资源，生成质量报告

**状态追踪格式**：`[MindFlow·${任务}·${步骤}/${迭代}·${状态}]`

</execution>

<references>

## 子技能

- **task:loop-planning** - 计划设计流程（深度研究、计划生成、计划确认）
- **task:loop-verification** - 验证流程（质量门控、持续改进决策）
- **task:planner** - 任务分解、依赖建模、资源分配
- **task:execute** - 并行编排、团队管理、进度跟踪
- **task:verifier** - 验收标准检查、质量评分
- **task:adjuster** - 失败分析、升级策略

## 详细文档

- [loop-deep-iteration.md](loop-deep-iteration.md) - 深度迭代完整实现
- [loop-detailed-flow.md](loop-detailed-flow.md) - 所有阶段详细代码

</references>

<quick_reference>

## 快速参考

**质量阈值**：第1轮 60分、第2轮 75分、第3轮 85分、第4+轮 90分

**失败策略**：retry(0s) → debug(2s) → replan(4s) → ask_user

**深度研究触发**：第1轮 | 失败2次 | 质量不达标 | 复杂任务

**Agent通信**：Agent 通过 SendMessage(@main) 上报，MindFlow 调用 AskUserQuestion

</quick_reference>

## 完成用户任务

用户任务目标：`$ARGUMENTS`

开始执行 MindFlow 流程，通过 PDCA 循环持续迭代，直到结果完全符合预期。
