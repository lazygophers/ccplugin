---
description: SKEIN 任务闭环入口 — 把请求强制作为 task 处理 (plan→exec→check→finish), 走动态 DAG 编排 + worktree 隔离 + 两层规则记忆
---

# skein-go

**有入参 `$ARGUMENTS`** → 把该请求**强制作为 SKEIN task 处理**, 不 inline 直接做 (即使看起来简单)。调用即「建 task 同意」信号。→ **加载 `skein-flow` skill 驱动该 task 走闭环** (plan→exec→check→finish 全流程由 skein-flow 承载, go 不复制)。

**无入参 (空)** → 不建新 task, **驱动 `.skein` 内所有既有 task 跑闭环**:
1. 跑 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py ready` (就绪批: pending+前置全 done+有空闲槽) 与 `skein.py current` (已 active)。
2. 无就绪且无 active → 报 "无待执行 task" 结束。
3. 有 → **对每个就绪/active task 加载 `skein-flow` skill 驱动其闭环** (flow = plan→exec→check→finish + worktree 隔离 + DAG 编排全流程; 已 planning 完成的从 exec 起, 未 planning 的先补 plan)。task 级并发上限 = `max_active` (默认 2, 见 `skein-flow` 多 task 并行调度), ready 即派 / 完成即派 / 冲突或 `depends_on` 未满足则串行等。
4. 全部 task done → 报告完成。

## 前置

- **无 `.skein/` 工作区** → 先跑 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py init` 初始化, 再继续。
- **判新旧**: 全新任务 → 新建; 对现有 active task 的补充/延续 → 并入 (`AskUserQuestion` 裁定不准的情况)。

## 强制流程 (不可跳步)

**由 `skein-flow` skill 承载** — go 只负责路由 (判有无入参 + 建/驱动 task), 闭环全流程 (0前置→plan→memory recall→激活→exec→check→finish) 见 `skein-flow` SKILL.md「强制流程」段, 分步细则见其 `references/mandatory-flow-steps.md`。go 不复制流程正文, 避免两处真值漂移。

## 边界

- 纯查询 / 单文件 ≤20 行且位置已知 → 豁免, 不建 task。
- 跨 ≥2 文件 / 多步骤 / 需调研 → 必建 task。
- 边界模糊 → `AskUserQuestion` 由用户裁定。

详见 `skein-flow` skill (强制闭环全规则)。
