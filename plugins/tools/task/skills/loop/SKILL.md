---
description: Loop 持续执行 - 作为 team leader 执行完整的任务管理循环，包括计划设计、执行、验证、调整
argument-hint: [ 任务目标描述 ]
skills:
  - task:planner
  - task:execute
  - task:verifier
  - task:adjuster
  - deepresearch:deep-research
model: sonnet
memory: project
---

<!-- STATIC_CONTENT: Cacheable (4800+ tokens) -->

# MindFlow - 迭代式任务编排引擎

<overview>

基于 PDCA 循环的智能任务编排引擎，通过持续迭代完成复杂任务。

**核心特性**：深度迭代（质量递进60→90分）、9状态生命周期、Team Leader（统一用户交互、调度4个agent）

</overview>

<execution>

## PDCA 流程

**Plan**（flows/plan）→ **Do**（task:execute）→ **Check**（flows/verify）→ **Act**（task:adjuster）

**7个阶段**：初始化 → 深度研究（可选）→ 计划设计 → 任务执行 → 结果验证 → 失败调整 → 完成

**状态追踪**：`[MindFlow·${任务}·${步骤}/${迭代}·${状态}]`

</execution>

<references>

## 子技能与文档

**子技能**：flows/plan（计划流程）、flows/verify（验证流程）、task:planner、task:execute、task:verifier、task:adjuster

**详细文档**：[deep-iteration实现](../deep-iteration/implementation.md)、[detailed-flow.md](detailed-flow.md)、[prompt-caching.md](prompt-caching.md)

</references>

<quick_reference>

质量阈值：60→75→85→90分 | 失败策略：retry→debug→replan→ask_user | 深度研究：第1轮/失败2次/质量不达标/复杂任务 | 缓存优化：静态内容标记，90%成本节省

</quick_reference>

<!-- /STATIC_CONTENT -->

<!-- DYNAMIC_CONTENT -->

用户任务：`$ARGUMENTS`

开始 PDCA 循环，持续迭代直到完全符合预期。

<!-- /DYNAMIC_CONTENT -->
