# trellisx 术语表 (CONTEXT)

> 经 `/grill-with-docs` 14 分支全量确认 (2026-06-29) 沉淀的核心术语。决策依据见 [adr/](adr/README.md)。

## 任务结构

| 术语 | 定义 |
| --- | --- |
| **task** | trellis 原生任务单元 = `.trellis/tasks/<dir>/` (task.json + prd.md + 复杂 task 的 design/implement/subtask)。生命周期: planning → in_progress → completed → archive |
| **parent / child** | 任务级关系 (顺序)。一个请求含 ≥2 独立可验收交付 → 拆 parent + 多 child。每 child 是独立 task, 完整生命周期。**child 调度动态** (见下) |
| **subtask** | 任务内执行单元 (非独立 task)。exec 含多独立无影响单元 → implement.md 拆 subtask。subtask ≠ child (正交) |

## 调度 (两层同构, 见 [ADR 0001](adr/0001-scheduler-is-main.md) + [0002](adr/0002-child-two-layer-scheduling.md))

| 术语 | 定义 |
| --- | --- |
| **main 调度器** | subtask 层唯一调度器。算冲突 → 建 DAG → 动态派 trellis-implement (并发2, 完成即派) → 收态 → 转 check |
| **parent 调度器** | child 层调度器 (持 child DAG)。独立 child 可并行 (各 worktree), 有依赖串行, 并发上限 2 |
| **trellis-implement** | 纯执行器。工具集仅 Read/Write/Edit/Bash, **无 Agent/Task** (Recursion Guard), 不调度不递归, 每次接 1 subtask |
| **5 态** | ready / blocked / running / done / failed (原 planned 并入 blocked) |
| **write-files / exec-scope** | subtask frontmatter 资源声明。write-files (写盘 glob) + exec-scope (none/package:pkg/project) 供 main 冲突判定 |

## 隔离

| 术语 | 定义 |
| --- | --- |
| **worktree 隔离单位 = task** | 默认 1 task 1 worktree (非 subagent 级, 非 subtask 级)。task 全部执行共享它 |
| **subtask 共享 task worktree** | 并行 subtask 在同一 task worktree 改不相交文件集, 不传 isolation:worktree, subtask 与 worktree 无绑定 |
| **多 worktree (opt-in)** | 用户显式同意才开 (大型并行隔离), 非自动, 非由 subtask 冲突触发 |

## 执行载体 (3 层, 见 [ADR 0003](adr/0003-main-no-source-write-default.md))

| 层 | 协调者 | 并发上限 | 适用 |
| --- | --- | --- | --- |
| main 直做 | — | 1 | ≤3文件/已知 file:line (只读探索 + 例外实施); **写源码默认禁** |
| sub-agent | main | 16 | 高量输出隔离 / 并行调研 / **实质实施默认走此** |
| agent-team | leader | 3-5 | 多假设辩论 / 跨层协调 |

**fork** = sub-agent 子选项 (继承对话上下文), 非独立层。

## 闭环 + 收尾

| 术语 | 定义 |
| --- | --- |
| **plan→exec→check→finish** | 强制四阶段闭环。未 archive 禁 Done |
| **finish AI 层** | finish 前 TaskList 查悬挂后台 agent → TaskStop 关 (Claude Code 专有) |
| **finish git 层** | trellisx-finish.py: commit → merge --no-ff (子先主后) → 销 worktree → archive |
| **guard Stop 两闸** | ①已合并未清理 worktree ②游离 worktree (tid=?/None)。原 "活动 task 未完成" 闸已移除 (用户: 不应禁 stop) |

## 看板

| 术语 | 定义 |
| --- | --- |
| **task.md 看板** | `.trellis/task.md` 单表格, 一行一 task, **5 列** (ID/名称/描述/状态/worktree) |
| **状态列** | 承载生命周期 (planning/exec/check/收尾/已完成/已归档)。hook sync 基础态不覆 AI 细分 |
| **唯一入口** | 经 trellisx-taskmd.py (sync/update/show/cleanup/lint/fix), 禁直编 |

## spec + grill

| 术语 | 定义 |
| --- | --- |
| **spec 破坏式 (主动化)** | 描述性 → 命令式契约 (MUST/禁/严禁)。**planning 自动加载** (grep 注入 PRD) + **finish 前自动 sediment** (软约束, 见 [ADR 0005](adr/0005-spec-proactive-loading.md)) |
| **sediment** | spec 增量沉淀模式 (≠ cortex, 见 [ADR 0004](adr/0004-decouple-cortex.md)) |
| **grill** | 对抗式审查, 贯穿 plan 前/中/后。只批注不改盘 (异步修复归 main)。可一次多问, 骨架可扩展动态 (默认 12 轴), 对象动态全产物 |

## 插件定位

| 术语 | 定义 |
| --- | --- |
| **改造工具 (非运行时)** | trellisx-apply 跑一次把 3 维度注入物内化进 `.trellis/`, trellis 原生机制接管。插件本身无运行时注入 hook |
| **guard (Claude Code 专属)** | 平台 hook 额外强制层 (Stop 两闸 + UserPromptSubmit 注入)。不强调跨平台; 核心自动化走 trellis 原生 hook |
