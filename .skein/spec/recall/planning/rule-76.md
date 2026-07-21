---
title: research 判定门 自动分档决策
layer: recall
category: planning
keywords: [research,判定,分档,自动判,planning,调研,灰区,信号]
source: -
authored-by: skein-spec
created: 1784629219
status: active
related: []
updated: 1784629219
---

## 触发场景
planning 阶段 brainstorm 前，需判断是否派 skein-researcher 调研。不是等用户说「要调研」才派，而是按信号**自动分档判定**。

## 陷阱 → 正解
**陷阱**: main 临场感觉或等用户明确说「要调研」才派 researcher → 容易漏调研或延后决策。
**正解**: brainstorm 前先跑判定门，按信号分档自动决策（明确需/明确不需/保守灰区/激进灰区/兜底）。

**陷阱**: 所有 task 都先调研一刀切 → 降效、浪费时间。
**正解**: 分档判定，明确不需的跳 research 直 brainstorm。

## 分档判定表
| 档 | 信号 | 判定 |
| --- | --- | --- |
| **明确需** | 外部 API / 库选型 / 跨陌生子系统 / 现状代码未知 / 协议待定 | **自动派 researcher** |
| **明确不需** | 已知代码模式 / 用户给足信息 / 单熟悉子系统 / 单点改 | **跳 research, 直 brainstorm** |
| **保守灰区** | 倾向需但不明确（可能涉未知但不确定） | **自动派 researcher**（宁可调研） |
| **激进灰区** | 倾向不需但拿不准（看似简单但可能有坑） | **AskUserQuestion 问用户是否需 research** |
| **兜底** | brainstorm 中 subtask 切不动 / depends_on 定不了 | **触发派 researcher** 勘察代码再拆 |

## 探索封顶
派 researcher 后仍受「探索封顶」约束 — 够拆 subtask 即收敛，禁无限深挖。researcher 的结论持久化在 `.skein/task/<id>/research/`，planning 后续步骤（brainstorm/PRD）可复读。

## 关联
- 铁律: hook 判定防自降级护栏 (core/planning/hook-prompt-judge-ai-only-57.md) — 互补，一个是 AI 自身判定，一个是是否派 subagent
- 实现细节: skein-plan SKILL.md §🧭 research 判定门 (2026-07-21落地)
