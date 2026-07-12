---
description: SKEIN 任务闭环入口 — 把请求强制作为 task 处理 (plan→exec→check→finish), 走动态 DAG 编排 + worktree 隔离 + 两层规则记忆
---

# skein-go

**有入参 `$ARGUMENTS`** → 把该请求**强制作为 SKEIN task 处理**, 不 inline 直接做 (即使看起来简单)。调用即「建 task 同意」信号。

**无入参 (空)** → 不建新 task, **驱动 `.skein` 内所有既有 task 跑闭环**:
1. 跑 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py ready` (就绪批: pending+前置全 done+有空闲槽) 与 `skein.py current` (已 active)。
2. 无就绪且无 active → 报 "无待执行 task" 结束。
3. 有 → 对每个 task 走下方「强制流程」的 exec→check→finish (已 planning 完成的从 exec 起; 未 planning 的先补 plan)。task 级并发上限 = `max_active` (默认 2, 见 `skein-flow` 多 task 并行调度), ready 即派 / 完成即派 / 冲突或 `depends_on` 未满足则串行等。
4. 全部 task done → 报告完成。

## 前置

- **无 `.skein/` 工作区** → 先跑 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py init` 初始化, 再继续。
- **判新旧**: 全新任务 → 新建; 对现有 active task 的补充/延续 → 并入 (`AskUserQuestion` 裁定不准的情况)。

## 强制流程 (不可跳步)

1. **plan** — 加载 `skein-planning` skill: 判新旧 + `skein.py create` 登记 + brainstorm 需求/方案 + grill 硬门 (必走)。产出 `prd.md`[+ `design.md`] + `implement.md`。
2. **memory recall** — 加载 `skein-memory` skill: 按任务描述召回相关 recall 规则注入上下文 (core 规则已常驻)。
3. **exec** — 加载 `skein-flow` skill (`references/scheduling-algorithm.md`): main 作调度器, 动态 DAG 为每个 subtask 选合适 agent (按任务性质挑现有 agent, 无合适的用 `general-purpose`) 各执行 1 subtask (并发上限 2, 完成即派), 全部改动落 task worktree, 主工作区零改动。
4. **check** — 加载 `skein-check` skill: 派 `skein-checker` 质量验证 (lint / type-check / tests / 契约合规); 未过 → 派合适 agent (无则 `general-purpose`) 定点修复重检。
5. **finish** — check 通过 → **sediment 判定门** (判本 task 有无 learning → core/recall/drop, 经 `skein-memory`) → `skein.py finish` (commit→merge→archive→销 worktree)。

## 边界

- 纯查询 / 单文件 ≤20 行且位置已知 → 豁免, 不建 task。
- 跨 ≥2 文件 / 多步骤 / 需调研 → 必建 task。
- 边界模糊 → `AskUserQuestion` 由用户裁定。

详见 `skein-flow` skill (强制闭环全规则)。
