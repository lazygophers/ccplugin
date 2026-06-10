---
name: trellisx-apply
description: 把 trellisx 的全部预想 (worktree 隔离 / subtask 编排 / main 协调 / trellis-check 闭环 / 回复前缀标记 / 前置流程铁律) 一次性内化进当前项目的 .trellis/ 自身 — 改 workflow.md (workflow-state 块 + Phase) + spec/ + trellis 生成的平台 hook。跑一次永久生效, 之后由 trellis 原生 hook 注入这些规则, 不需 trellisx 运行时 hook。幂等 (marker 包裹, 重复跑只更新不堆叠)。
when_to_use: 用户主动在某 trellis 项目内运行, 把该项目的 .trellis 改造成符合 trellisx 规范。短语 "trellisx apply" "应用 trellisx" "改造 .trellis" "内化 trellisx 规则" "/trellisx-apply"。
argument-hint: [scope]
arguments: [范围]
---

# trellisx-apply — 把 trellisx 规则内化进 .trellis

把 trellisx 的设计 (见 §规则集) **一次性写进当前项目的 `.trellis/` 自身**, 让 trellis 原生流程内置这些约束。跑完后 trellisx 不再需要运行时 hook —— trellis 自己的 `inject-workflow-state` hook 每轮就会注入这些规则。

## 立场

| 立场 | 说明 |
| --- | --- |
| 内化优于外挂 | 规则写进 `.trellis/`, 由 trellis 自身机制生效; 不靠 trellisx 持续 hook |
| 幂等 | 所有注入用 `<!-- trellisx:start:<key> -->...<!-- trellisx:end:<key> -->` marker 包裹; 重复跑只更新 marker 内, 不重复堆叠 |
| 尊重 trellis 原生 | 融合而非取代: 引用 trellis 已有 (task.py / add-subtask / jsonl / trellis-check), 仅补 trellis 缺的 (worktree / subtask 文件编排) |
| 显式审批 | 改 `.trellis/` 前展示 diff plan, 经用户批准 (AskUserQuestion) 才写盘 |

## 前置检查

```bash
ls .trellis/ || { echo "非 trellis 项目, 终止"; exit 1; }
ls .trellis/workflow.md          # 注入目标
ls .trellis/spec/ 2>/dev/null    # spec 目标
ls .claude/hooks/ 2>/dev/null    # 平台 hook 目标 (trellis init --claude 生成)
```

非 trellis 项目 → 报错终止。

## 工作流 (5 步)

| 步骤 | 行动 | 详细内容 |
| --- | --- | --- |
| 1 | 诊断 .trellis 现状 + 检测已有 trellisx marker | 读 `references/diagnose.md` |
| 2 | 注入 workflow.md (workflow-state 块 + Phase 描述) | 读 `references/workflow-injection.md` |
| 3 | 注入 spec/ (trellisx 规范文档) | 读 `references/spec-injection.md` |
| 4 | 注入平台 hook (worktree 自动建/销) | 读 `references/hook-injection.md` |
| 5 | AskUserQuestion 审批 → 一次写盘 → 验证 | 读 `references/apply-verify.md` |

## 规则集 (内化的 trellisx 预想)

注入到 `.trellis/` 的全部规则 (C1-R5 决策已落定):

| 规则 | 内容 | 落地位置 |
| --- | --- | --- |
| **任务门禁** | 实施 (写盘) 无条件建 task; 探索 (只读) 按复杂度 | workflow.md `[workflow-state:no_task]` |
| **subtask 拆分** | task 拆 ≥ 2 subtask, 各独立可验收 | workflow.md `[workflow-state:planning]` + spec |
| **main 角色 (C1)** | main **可直接写源码** (trellis inline 风格), **但必须在 worktree 内**; 复杂/并行派 sub-agent / agent-team | workflow.md `[workflow-state:in_progress]` |
| **worktree (I1/I2)** | `task.py start` 后建 `.trellis/worktrees/<task>` worktree; 执行限于 worktree; archive 时合并 + 移除 | workflow.md + 平台 hook (PostToolUse 监测 task.py) |
| **trellis-check 闭环 (C3)** | task 完成前**必经** `trellis-check`; 未过禁宣告完成 | workflow.md 完成判定 + spec |
| **回复前缀标记** | 所有回复以 `[trellisx-{status}-{task}]` (无 task `[trellisx]`) 开头 | workflow.md 顶部 + 平台 hook |
| **前置流程铁律** | 确认实施 → ①create ②planning拆subtask ③worktree ④execute ⑤trellis-check | workflow.md Phase 描述 |
| **subtask 文件编排 (R2)** | 每 subtask 独立文件 `.trellis/tasks/<task>/subtask/<id>.md` + mermaid 调度图 | 引用 `trellisx-orchestrate` skill |
| **spec 优化 (R4)** | 破坏式重写走 `trellisx-spec`; 增量捕获走 trellis 原生 `trellis-update-spec` | spec 说明 |
| **jsonl (R5)** | implement.jsonl/check.jsonl 由 trellis 平台 hook 自动注入, 仅说明 curate 填什么 | 引用 trellis |

## 参考集 (按需读)

| 文件 | 用途 |
| --- | --- |
| `references/diagnose.md` | 步骤 1: 现状诊断 + marker 检测 |
| `references/workflow-injection.md` | 步骤 2: workflow-state 块 + Phase 注入内容 (核心) |
| `references/spec-injection.md` | 步骤 3: spec 规范文档 |
| `references/hook-injection.md` | 步骤 4: 平台 hook worktree 自动化 + 前缀注入 |
| `references/apply-verify.md` | 步骤 5: 审批 + 写盘 + 验证 |

## 相关 skill

- `trellisx-orchestrate` — planning 阶段编排 PRD/design/implement/subtask (被内化的 workflow 引用)
- `trellisx-spec` — spec 破坏式优化
