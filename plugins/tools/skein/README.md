# SKEIN

**独立任务管理插件** — 零 trellis / trellisx 依赖, 自带 `.skein/` 工作区。名取「线团」(skein of yarn): 任务如纱线, 编织、调度、收束。

## 能做什么

| 能力 | 载体 | 说明 |
| --- | --- | --- |
| 强制 task 闭环 | `skein-flow` | 请求强制走 plan→exec→check→finish, 不 inline |
| 动态 DAG 编排调度 (双层) | `skein-orchestrate` | main 作调度器, task 级 + subtask 级同构, 冲突自算边 + `depends_on`, 并发上限 2, 完成即派 |
| worktree 隔离 | `skein.py` | 1 task 1 worktree, 主工作区零改动 |
| 看板 | `skein.py board` | `.skein/task.md` 生命周期看板 (脚本渲染) |
| planning 入口 | `skein-planning` | 判新旧 + 登记 + brainstorm + grill 硬门 (必走) |
| **两层×类目规则记忆** | `skein-memory` + `memory.py` | **差异化核心** (见下) |
| 对抗式审查 | `skein-grill` | 需求/工件对抗校对 (planning 硬门) |
| 破坏式重构 | `skein-refactor` | 不保兼容、全站点一次改齐的重构执行器 |
| 质量门 | `skein-check` | 派 `skein-checker` 验证 (lint/type/test/契约), 未过派 `skein-implementer` 修复重检 |
| 第 3 轮根因复盘 | `skein-break-loop` | check 第 3 轮仍 FAIL 时跨维度结构化根因复盘 (需求/设计/实现/环境/测试 5 维 + 预防措施), 出口回 exec 定向重修或 STOP 转人工 |
| 冷启动播种 | `skein-bootstrap` | 空仓首次接入时扫既有代码库约定 (命名/错误处理/测试/架构边界/构建) 播种规则基线 (一次性, 默认多归 recall) |
| 归档清理 | `skein-clean` | 孤儿 worktree / 悬挂分支 / 漏归档安全清扫 |

3 个执行 agent (均无 Agent/Task 工具, 递归护栏): `skein-implementer` (worktree 内执行 1 subtask, 每文件过写前 CHECKPOINT) / `skein-checker` (只读验证) / `skein-researcher` (planning 调研 + bootstrap 扫描模式)。

## 差异化核心: 两层规则记忆 (基于 `.claude/rules`)

不同于 spec 式「按需沉淀单一文件」, SKEIN 记忆分两层:

- **core (常驻)** — `.claude/rules/core/<类目>/*.md`: 每 session 自动注入的硬规 / 命令式契约。适合「后续同类任务必再踩」的强约束。
- **recall (按需)** — `.claude/rules/recall/<类目>/*.md`: 存盘, 按任务语义相关性检索注入。适合长尾、上下文密集的经验, 不占常驻上下文。

**两层 × 类目**: 层内按类目 (git/test/arch/build/style/domain/ops...) 分子目录, 自由取名按需建。索引三份: 每层 `<layer>/index.md` + 顶层 `index.md` (两层聚合), sediment 写盘后自动 reindex。

**sediment 判定门**: 每个 task finish 后, 按 checklist 判本次 learning 应 → `core` / `recall` / `drop`, 经审批写盘。频率驱动的 core↔recall 升降级为可选演进 (按需再加)。

## 工作区

```
.skein/
├── task.md            # 看板 (经 skein.py board 渲染, 禁直接编辑)
├── state.json         # {focus: <当前 task id>}
├── config.json        # {max_active:2, auto_commit:true, worktree_root:".worktrees"}
└── task/
    ├── <id>/          # 活跃 task: prd.md / design.md / implement.md / task.json
    └── archive/<年>/<月-日>/<id>/   # 按完成日期分层归档
.claude/rules/
├── index.md                      # 顶层索引 (两层聚合概览)
├── core/{<类目>/*.md,index.md}   # 常驻规则 (按类目分子目录) + 层索引
└── recall/{<类目>/*.md,index.md} # 按需召回规则 (按类目分子目录) + 层索引
```

> SKEIN 自包含: `skein.py` 自身即引擎, `config.json` 是纯设置 (无外部生命周期 hook 层), start/finish 直接干活。


## 用法

```
/skein-go <任务描述>
```

或直接触发 `skein-flow` skill (复杂/多步/跨文件请求自动加载)。

## 完整文档

`docs/` 有完整文档 (从 [docs/README.md](docs/README.md) 起):

| 想 | 读 |
| --- | --- |
| 装好插件跑通第一个 task | [docs/getting-started.md](docs/getting-started.md) |
| 搞懂内部运转 (流程/调度/记忆) | [docs/workflow.md](docs/workflow.md) |
| 不同活儿分别怎么用 | [docs/scenarios.md](docs/scenarios.md) |
| 最佳实践 + 流程图 | [docs/best-practices.md](docs/best-practices.md) |
| CLI/skill/agent 速查 | [docs/reference.md](docs/reference.md) |

## License

AGPL-3.0-or-later
