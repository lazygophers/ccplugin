# SKEIN

**独立任务管理插件** — 零 trellis / trellisx 依赖, 自带 `.skein/` 工作区。名取「线团」(skein of yarn): 任务如纱线, 编织、调度、收束。

## 能做什么

| 能力 | 载体 | 说明 |
| --- | --- | --- |
| 强制 task 闭环 | `skein-flow` | 请求强制走 plan→exec→check→finish, 不 inline |
| 动态 DAG 编排调度 | `skein-orchestrate` | main 作调度器, 冲突自算边 + `depends_on`, 并发上限 2, 完成即派 |
| worktree 隔离 | `skein.py` + `worktree.py` | 1 task 1 worktree, 主工作区零改动 |
| 看板 | `skein-workspace` + `taskmd.py` | `.skein/task.md` 生命周期看板 |
| planning 入口 | `skein-add` | 判新旧 + 登记 + brainstorm + grill 硬门 |
| **两层规则记忆** | `skein-memory` | **差异化核心** (见下) |
| 对抗式审查 | `skein-grill` | 需求/工件对抗校对 |
| 破坏式重构 | `skein-spec` | 跨任务破坏式代码变更执行器 |
| 内化注入 | `skein-apply` | 规则内化进 `.skein` config hook |
| 归档清理 | `skein-cleanup` | 完成后归档、销 worktree、清看板 |

## 差异化核心: 两层规则记忆 (基于 `.claude/rules`)

不同于 spec 式「按需沉淀单一文件」, SKEIN 记忆分两层:

- **core (常驻)** — `.claude/rules/core/*.md`: 每 session 自动注入的硬规 / 命令式契约。适合「后续同类任务必再踩」的强约束。
- **recall (按需)** — `.claude/rules/recall/*.md`: 存盘, 按任务语义相关性检索注入。适合长尾、上下文密集的经验, 不占常驻上下文。

**sediment 判定门**: 每个 task finish 后, 按 checklist 判本次 learning 应 → `core` / `recall` / `drop`, 经审批写盘。频率驱动的 core↔recall 升降级为可选演进 (按需再加)。

## 工作区

```
.skein/
├── task.md            # 看板 (经 taskmd.py, 禁直接编辑)
├── tasks/<id>/        # 每 task: prd.md / design.md / implement.md / task.json
├── archive/           # 归档已完成 task
└── config.yaml        # 生命周期 hook (after_finish 等)
.claude/rules/
├── core/*.md          # 常驻规则
└── recall/*.md        # 按需召回规则
```

## 用法

```
/skein-go <任务描述>
```

或直接触发 `skein-flow` skill (复杂/多步/跨文件请求自动加载)。

## License

AGPL-3.0-or-later
