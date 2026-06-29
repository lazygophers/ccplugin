# trellisx 核心概念

## 1. task

trellis 原生任务单元。一个 task = `.trellis/tasks/<task-dir>/` 目录, 含 `task.json` (状态) + `prd.md` (+ 复杂 task 的 `design.md` / `implement.md` / `subtask/*.md`)。

生命周期: `planning` → `in_progress` (task.py start) → `completed` (task.py finish) → archive。

trellisx 不改 task 定义, 只在其上叠加 worktree 隔离 / subtask 编排 / 闭环 / 看板。

## 2. parent/child (任务级, 依次) ≠ subtask (任务内, 并行)

**这是最容易混淆的一对, 必须分清。**

### parent/child — 任务级, 依次执行

- 触发: 一个请求含 **≥ 2 个独立可验收交付** → 拆 parent + 多 child (`task.py create --parent`)。
- 每个 child 是**独立 task**, 完整生命周期 (plan/impl/check/archive)。
- child **依次执行** (按依赖顺序, 一个 archive 再启下一个), **非并行**。
- parent 持 child map + 跨 child 验收 + 集成 review, 通常不直接做实施。

### subtask 拆分 — 任务内 exec, 动态调度

- 触发: **任一 task** (含每个 child) 的 exec 含**多独立无影响单元** → `implement.md` 拆 subtask。
- **main 是调度器**: 算冲突 (写盘 glob 相交 + 执行作用域相交 + 显式依赖) → 建 DAG → 动态派 `trellis-implement` 各执行 1 subtask (并发上限 2, 完成即派下一个)。
- **trellis-implement 不调度不递归** (工具集无 Agent/Task, Recursion Guard); 每 subtask 文件声明 `write-files` + `exec-scope` 供冲突判定。
- subtask 是**任务内执行单元**, 不是独立 task。

### 对比

| | parent/child | subtask |
| --- | --- | --- |
| 层级 | 任务级 | 任务内 exec |
| 各自是 task? | 是 (独立生命周期) | 否 (执行单元) |
| 执行方式 | 依次 (按依赖) | 动态调度 (无依赖并发, 上限 2) |
| 拆分信号 | 多独立可验收交付 | 单 task 内多独立无影响单元 |
| 工具 | `task.py create --parent` / `add-subtask` | `implement.md` + subtask 文件 |

> child ≠ subtask。child 自身的 exec 也可再 subtask 拆分。

## 3. worktree 隔离单位 = task (非 subtask)

### 模型

- **隔离单位是 task, 不是 subagent**: `task.py start` 时 after_start hook 自动建**本 task 的** worktree。
- **默认 1 task 1 worktree**: 该 task 全部执行 (main / sub-agent / agent-team / workflow agent) 都在此 worktree 内。
- **subtask 共享 task worktree**: 并行 subagent 在同一 task worktree 内改**不相交文件集**即可, 不传 `isolation:worktree`, subtask 与 worktree**无绑定**。
- **多 worktree 属 opt-in**: 用户显式同意一个 task 多 worktree 才开 (如大型并行隔离), 非自动, 非由 subtask 冲突触发; finish 合并各分支。

### 为何 task 级

worktree 防**并发多 task** 互相冲突。同 task 内并行 subagent 共享 worktree 改不相交文件集即可 (PRD 调度图保证文件集不相交, 共享文件走串行)。

### 豁免

`--no-worktree`: subagent 改主工作区 (无 worktree 分支可合并, finish 跳过合并/销 worktree, 直接 commit 主工作区 + archive)。但 main 禁亲改源码这条 `--no-worktree` 不豁免。

## 4. 执行载体 4 层

design / implement 标注每块工作的执行层。planning 定层, dispatch 直接读不重判。

| 层 | 协调者 | 上下文 | 并发上限 | 适用 |
| --- | --- | --- | --- | --- |
| main 直做 | — | 主对话 | 1 | ≤ 3 文件 / 已知 file:line; 实施类必在 task worktree 内写 |
| sub-agent | main 逐轮决策 | 隔离 context window | 16 (机器上限) | 高量输出隔离 / 并行调研 / 强约束工具 |
| agent-team | leader 协调 + 共享任务列表 | 每 teammate 独立 | 3-5 推荐 | 多假设辩论 / 跨层协调 / 多视角审查 |
| workflow | 脚本 | 脚本变量持有中间结果 | 16 并发 / 1000 总 | 仓库级审计 / 大规模迁移 / 多源交叉验证 |

**默认载体 = subagent 编排** (绝大多数 task 够用)。**Workflow 仅特别复杂 task** (大规模 fan-out / 仓库级 / ≥5 同类文件 / 500+ 文件迁移) 用户显式同意才启。

> sub-agent / agent-team / workflow agent 都在**本 task worktree 内**执行 (共享), 禁在主工作区写盘。唯一例外: 纯只读 sub-agent (探索/调研/审查)。

> **调度权归 main**: subtask 的动态调度 (算冲突 / 建 DAG / 派发 / 收态 / 转 check) 由 **main** 负责, 非 trellis-implement。trellis-implement 工具集仅 Read/Write/Edit/Bash, **无 Agent/Task** (Recursion Guard), 物理上不能调度/派 subagent/递归 —— 它只执行被派的 1 个 subtask。每个 subtask 文件声明 `write-files` (写盘 glob) + `exec-scope` (执行作用域 `none`/`package:<pkg>`/`project`) 供 main 做冲突判定。详见 orchestrate skill `scheduling.md`。

## 5. plan → exec → check → finish 闭环

强制四阶段串成环, 每阶段衔接无断点:

| 阶段 | 动作 | 产物 |
| --- | --- | --- |
| plan | trellisx-orchestrate 编排 | prd.md (+ design.md + implement.md + subtask/*.md) |
| exec | main 调度派 trellis-implement 各执行 1 subtask (动态 DAG, 共享 task worktree) | 源码改动 (落 worktree) |
| check | trellis-check | check 报告 |
| finish | AI 层 (TaskStop 清悬挂) + git 层 (finish.py: commit→merge→销→archive) | archived task |

**闭环硬规**: 未 archive 禁宣告 Done (软约束, AI 有裁量; guard 在 Claude Code 额外 block)。

### finish 收尾两层 (顺序: 先 AI 层后 git 层)

- ⓪ **AI 层** (脚本做不到): finish 前 `TaskList` 查本 task 名下悬挂 Workflow/后台 agent, 逐个 `TaskStop` 关。
- ① **git 层** (确定性脚本 `trellisx-finish.py`): commit→merge --no-ff (子先主后)→销 worktree→archive。

`finish.py` 只销 worktree (git), 关闭 Workflow/Task 是 AI 层职责。

### 动态调度 (exec 阶段, main 调度器)

exec 阶段 subtask 调度由 **main** 动态驱动 (非 trellis-implement):

- **资源声明**: 每 subtask 文件 frontmatter 填 `write-files` (写盘 glob) + `exec-scope` (`none` / `package:<pkg>` / `project`)。
- **冲突判定** (planning 末 main 静态算): 两 subtask 有依赖边 ⟺ ①写盘 glob 相交 ②执行作用域相交 (同包 or 任一 project) ③显式 depends-on。无依赖边 = 可并行。
- **5 态**: `ready` / `blocked` / `running` / `done` / `failed` (原 planned 并入 blocked)。
- **调度循环** (并发上限 2): 查 ready → 派 min(|ready|, 2-|running|) 个 trellis-implement 各执行 1 subtask → 任一返回 (notification) 即更新态、查新 ready、立即派下一个 (不空等全部) → failed 走 failure-recovery → 全 done 转 trellis-check。
- **trellis-implement 纯执行**: 工具集无 Agent/Task (Recursion Guard), 不调度不递归; 每 subtask 各派 1 个, 共享 task worktree 改不相交文件集。

详见 orchestrate skill `scheduling.md`。

## 6. task.md 看板

trellis 原生有每任务 `task.json`, 但无跨任务总览。trellisx 维护 `.trellis/task.md` 作为人类可读看板 —— **一个表格, 一行一个 task**。

**维护者按列分工**:
- trellis 生命周期 hook (`trellisx-taskmd.py`): 自动维护确定性列 (ID/名称/描述/状态) + 7 天清理。
- AI (trellisx-workspace skill): 维护主观列 (阶段/进度/worktree 路径)。
- 同行不同列互不覆盖。

**唯一入口**: 一律经 `.trellis/scripts/trellisx-taskmd.py`, 禁直接编辑 task.md。task.md 落后于 task.json = 看板失效, 视为流程缺陷。

## 7. spec 破坏式优化

trellisx-spec 把 `.trellis/spec/` 描述性条款改为**可机器验证的命令式契约** (MUST / 禁 / 严禁)。允许破坏式变更 (丢弃旧版本/合并/拆分/推翻原结构), 但**必须走 AskUserQuestion 审批门** (所以 main 直接执行, 非 fork subagent)。

## 8. 概念速查

| 问 | 答 |
| --- | --- |
| 一个 task 默认几个 worktree? | 1 个 |
| 并行 subtask 各开 worktree? | 否, 共享 task worktree |
| child 之间并行? | 否, 依次 (按依赖) |
| 子任务并行? | 动态调度 (无依赖并发, 上限 2) |
| 何时多 worktree? | opt-in, 用户显式同意 |
| 未 archive 能宣告 Done? | 否 |
| finish 谁关 Workflow/Task? | AI 层 (TaskStop), 脚本只销 worktree |
| 看板怎么改? | 只能经 trellisx-taskmd.py |
