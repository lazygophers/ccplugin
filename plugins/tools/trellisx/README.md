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

## 注入维度 (纯增量, 不改原生流程)

apply **只增加** worktree + subtask 两个维度, **绝不修改** trellis 原生 task 创建 / check / finish / 前缀:

| 维度 | 内容 |
| --- | --- |
| subtask 拆分 | planning 块加 拆 ≥ 2 subtask + 独立文件 + 调度图 |
| worktree 隔离 | in_progress 块加 worktree; task.py start 自动建 .trellis/worktrees/<task>, archive 销毁 (平台 hook, 不改 task.py) |

绝不碰: no_task (task 创建触发) / Phase 流程 / 完成判定 / 前缀 — 全保持 trellis 原生。

## 与 trellis 融合 (非取代)

| 能力 | 用谁 |
| --- | --- |
| task.py / add-subtask / implement / check / update-spec / jsonl | trellis 原生 |
| worktree 隔离 + subtask 文件编排 + 破坏式 spec + 前缀 | trellisx (补 trellis 缺的) |

## 用法

在 trellis 项目内运行 `/trellisx-apply` → 诊断 → 注入 plan → AskUserQuestion 审批 → 写盘 → 验证 → 重启会话生效。幂等可重复跑。

## 安装

通过 ccplugin-market 安装。
