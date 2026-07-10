---
description: SKEIN 任务闭环入口 — 把请求强制作为 task 处理 (plan→exec→check→finish), 走动态 DAG 编排 + worktree 隔离 + 两层规则记忆
---

# skein-go

把用户请求 `$ARGUMENTS` **强制作为 SKEIN task 处理**, 不 inline 直接做 (即使看起来简单)。调用即「建 task 同意」信号。

## 前置

- **无 `.skein/` 工作区** → 先跑 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py init` 初始化, 再继续。
- **判新旧**: 全新任务 → 新建; 对现有 active task 的补充/延续 → 并入 (`AskUserQuestion` 裁定不准的情况)。

## 强制流程 (不可跳步)

1. **plan** — 加载 `skein-add` skill: 判新旧 + `skein.py create` 登记 + brainstorm 需求/方案 + grill 硬门。产出 `prd.md`[+ `design.md`] + `implement.md`。
2. **memory recall** — 加载 `skein-memory` skill: 按任务描述召回相关 recall 规则注入上下文 (core 规则已常驻)。
3. **exec** — 加载 `skein-orchestrate` skill: main 作调度器, 动态 DAG 派 subagent 各执行 1 subtask (并发上限 2, 完成即派), 全部改动落 task worktree, 主工作区零改动。
4. **check** — 派 subagent 质量验证 (lint / type-check / tests / spec 合规); 未过 → 修复重检。
5. **finish** — check 通过 → **sediment 判定门** (判本 task 有无 learning → core/recall/drop, 经 `skein-memory`) → `skein.py finish` (commit→merge→archive→销 worktree)。

## 边界

- 纯查询 / 单文件 ≤20 行且位置已知 → 豁免, 不建 task。
- 跨 ≥2 文件 / 多步骤 / 需调研 → 必建 task。
- 边界模糊 → `AskUserQuestion` 由用户裁定。

详见 `skein-flow` skill (强制闭环全规则)。
