# 步骤 3: spec/ 注入

在 `.trellis/spec/` **新增**一个 trellisx 规范文档 (作为 workflow.md 注入的详细背书)。

**边界**: apply **只新增** `trellixx-conventions.md` 一个文件, **绝不修改/重构用户原有的 spec 内容**。spec 的破坏式优化/重写是 `trellisx-spec` skill 的职责 (用户单独主动调用), 与 apply 无关。

## 注入文件: `.trellis/spec/guides/trellisx-conventions.md`

```markdown
---
updated: <ISO date>
authored-by: trellisx-apply
---

# trellisx 任务编排约定

何时被读: trellis task 实施 / 检查时 (sub-agent dispatch 注入)
谁读: main / trellis-implement / trellis-check / 任何执行者
不遵守的代价: worktree 污染主工作区 / task 无隔离 / 流程跳步

## worktree 隔离 (trellisx 补 trellis 缺失)

- task.py create/start 后自动建 worktree (git 根 `.trellisx-worktrees/<service>/<task>`, 自适应微服务 + sparse; 平台 hook trellisx-worktree.py)
- 全部源码改动**必须**落 worktree 内, 主工作区保持干净
- main 可直接写源码 (trellis inline), 但目标路径必须在 worktree
- 复杂 / 并行 subtask → 派 sub-agent (isolation:worktree) 或 agent-team 成员
- task archive 时: worktree 干净 → 自动销毁; 脏 → 警告先合并

## 标准开发流程 (5 步)

① 创建任务 + 切 worktree (task.py create+start, 自动建 .trellis/worktrees/<task>)
② 任务规划 (拆 ≥ 2 subtask, 写 prd/design/implement + subtask 文件 + 调度图)
③ 异步执行 (按调度图调度 subtask agent, 无依赖的并行派发提效)
④ 整体 trellis-check 校验 (闭环)
⑤ commit + finish (合并移除 worktree → commit → archive → 落 cortex)

## subtask 拆分

- task 必须拆 ≥ 2 subtask (按 实施/验证/文档 维度)
- 每 subtask 独立文件 `.trellis/tasks/<task>/subtask/<id>-<slug>.md` (见 trellisx-orchestrate skill)
- PRD 含 mermaid 调度图 (依赖 + 并行)
- parent-child 用 trellis 原生 `task.py add-subtask`

## 分工 (融合 trellis 原生)

| 能力 | 用谁 |
| --- | --- |
| 建 task / start / archive / add-subtask | trellis 原生 `task.py` |
| 实施 / 检查闭环 | trellis 原生 `trellis-implement` / `trellis-check` |
| 增量 spec 捕获 | trellis 原生 `trellis-update-spec` |
| 破坏式 spec 重写 | trellisx `trellisx-spec` skill |
| planning 文档编排 (PRD/design/implement/subtask 文件 + 调度图) | trellisx `trellisx-orchestrate` skill |
| worktree 隔离 + 前缀标记 | trellisx (本约定 + 平台 hook) |

```

## 幂等

文件整体重写 (apply 拥有该文件), frontmatter `updated` 刷新。文件名固定 `trellixx-conventions.md`, 重复 apply 覆盖更新。

## workflow.md 被 trellis update 覆盖的备份说明

workflow.md 注入可能被 `trellis update` 覆盖 (模板 hash)。本 spec 文档是 workflow 注入的**持久备份** —— 即使 workflow marker 丢失, 规则仍在 spec; 重跑 `trellisx-apply` 可恢复 workflow 注入。
