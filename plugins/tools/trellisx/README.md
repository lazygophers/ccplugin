# trellisx

Trellis **增强改造工具**。跑一次 `trellisx-apply`, 把 trellisx 的全部预想 (worktree 隔离 / subtask 编排 / main 协调 / trellis-check 闭环 / 回复前缀标记 / 前置流程铁律) **内化进项目的 `.trellis/` 自身** —— 之后由 trellis 原生机制注入这些规则, 不靠 trellisx 运行时 hook。

## 定位

```
早期: trellisx = 外部一堆 command hook 持续拦截/注入 (复杂, 需 reload, 易冲突)
现在: trellisx = 改造工具, 跑一次写进 .trellis (规则内化, trellis 自身机制生效)
```

trellisx 插件本身**无运行时 hook**。worktree 自动化 hook 由 `trellisx-apply` 写进**用户项目**的 `.claude/hooks/`。

## Skills (3)

1. **`trellisx-apply`** (核心) — 用户主动跑一次, 改造当前项目 `.trellis/`:
   - `workflow.md`: workflow-state 块 + Phase 注入规则 (marker 幂等)
   - `.trellis/spec/guides/trellixx-conventions.md`: 规范文档 (持久备份)
   - `.claude/hooks/trellisx-worktree.py`: PostToolUse 监测 `task.py start/archive` 自动建/销 worktree (不改 task.py)
   - `.trellis/.gitignore`: 排除 `worktrees/`
2. **`trellisx-orchestrate`** — planning 编排 PRD/design/implement/subtask 文件 + mermaid 调度图
3. **`trellisx-spec`** — spec 破坏式优化 (增量捕获走 trellis 原生 trellis-update-spec)

## Agent (1)

- **`trellisx-spec`** — forked subagent, 仅读写 `.trellis/spec/**`

## 内化规则 (C1-R5)

| 规则 | 内容 |
| --- | --- |
| 任务门禁 | 实施建 task; 探索按复杂度 |
| subtask 拆分 | task 拆 ≥ 2 subtask + 调度图 |
| main 角色 (C1) | main 可写源码 (inline) 但必须在 worktree; 复杂/并行派 agent |
| worktree (I1/I2) | task.py start 自动建 .trellis/worktrees/<task>; archive 干净则销毁 |
| trellis-check 闭环 (C3) | 完成前必经 trellis-check |
| 回复前缀 | 所有回复 [trellisx-{status}-{task}] (无 task [trellisx]) |

## 与 trellis 融合 (非取代)

| 能力 | 用谁 |
| --- | --- |
| task.py / add-subtask / implement / check / update-spec / jsonl | trellis 原生 |
| worktree 隔离 + subtask 文件编排 + 破坏式 spec + 前缀 | trellisx (补 trellis 缺的) |

## 用法

在 trellis 项目内运行 `/trellisx-apply` → 诊断 → 注入 plan → AskUserQuestion 审批 → 写盘 → 验证 → 重启会话生效。幂等可重复跑。

## 安装

通过 ccplugin-market 安装。
