# 运行机制

本篇讲 SKEIN 内部怎么转: 谁在调度、任务怎么闭环、并行怎么调、记忆怎么沉淀。

## 角色分工

| 角色 | 是谁 | 干什么 | 有 Agent/Task 工具? |
| --- | --- | --- | --- |
| **main** | 主对话 (coordinator) | 调度器: 跑 `skein.py` 脚本、派 subagent、与你交互决策、回传进度、维护看板 | 有 (能派) |
| **skein-implementer** | 执行 agent | worktree 内执行 **1 个** subtask, 写代码 | 无 (递归护栏) |
| **skein-checker** | 验证 agent | 只读, 跑 lint / type / test / 契约校验 | 无 |
| **skein-researcher** | 调研 agent | planning 纯信息调研 (选型 / 对比); **bootstrap 扫描模式** 扫既有代码库约定提炼候选规则, 结论落盘 `research/` | 无 |

**铁律**: main 默认**不亲自写源码** — 实质产出派具名 subagent。3 个执行 agent 都**没有** Agent/Task 工具, 不能自派 (Recursion Guard), 各自只干一件事。

`skein.py` 的 `create/start/finish/archive` 是任务记录管理, 由 main **同步**直接跑, 不派 agent、不算实质工作。

## 强制闭环: plan → exec → check → finish

不可跳步。**未 archive = 未完成**。完整 7 步 (含前置与激活):

```
前置 → plan → memory recall → 激活(grill 硬门) → exec → check → finish
```

### ① plan (main 同步, 交互式)

- **判新旧**: 全新任务 → `skein.py create` 登记; 对现有 active task 的补充 → 并入 (判不准就 AskUserQuestion 问你)。
- **brainstorm**: main 和你梳理需求与方案 (subagent 不能与你对话, 故全程 main 前台)。
- **grill 硬门**: 对抗式审查需求与工件, 弱点补齐后才放行。**未跑 grill 禁进 exec**。
- **契约锁定** (可选增强): planning / grill 时把不可回退的不变量逐条 `skein.py contract <id> --add "文本"` 锁进 task.json, 供 ⑤ check 逐条验证。
- 产出: `prd.md` (+ 需要时 `design.md`) + `implement.md`, 请你评审 (AskUserQuestion)。

### ② memory recall (main 同步)

按任务描述从 `recall` 层召回相关规则注入上下文 (`core` 规则已在 session 开始时常驻注入)。让本 task 带上项目历史经验。

### ③ 激活 (main 同步)

grill 通过 + 你评审确认 → `skein.py start`:

- 建 git worktree: `git worktree add -b skein/<id> .worktrees/skein-<id> HEAD`
- task 状态 → `in_progress`, 写入 worktree 路径, 设为 focus。
- 检查前置 (`deps`) 都完成、active 集未超上限 2。

### ④ exec (main 调度 + subagent 执行)

main 作调度器跑**动态 DAG 调度循环**:

- 把 `implement.md` 拆成 subtask, 按冲突自算边 + 显式 `depends_on` 组成 DAG。
- **ready 即派** `skein-implementer` (6 字段自包含 prompt), **并发上限 2**, **完成即派**下一个 (不空等全部)。
- **读后写硬门 + reason 注解**: dispatch prompt 的「工作目录与范围」段**逐文件枚举**, 每个文件带 **reason** (改它满足哪条契约/需求)。implementer 收 subtask 后, 对每个待改文件必过 **写前 CHECKPOINT**: 先 `Read` 全文 → 复述适用契约 + reason → 才 `Edit`/`Write`; 若文件现状与契约矛盾, 标 `需要:` 回传, **不擅改**。把契约约束从 check 事后验**前移到写前** (契约仍是 planning 锁进 task.json 的同一份, 不重造)。
- 所有改动落 task worktree, 主工作区零改动。
- 每个 agent 完成 / 阻塞 → main **立即**回传摘要 (禁批量延迟)。
- 派出异步任务后结束本回合前, MUST 输出任务全景表 (状态: 进行中 / 等待中 / 阻塞)。

### ⑤ check (main 派 checker fan-out)

派 `skein-checker` 验证 spec 合规 / lint / type / tests。checker 先 `skein.py contract <focus>` 读出 planning 阶段锁定的契约, **逐条验证 pass/fail** (不变量守住没)。未过 → 派 `skein-implementer` 定点修复重检, 不跳 finish。

**第 3 轮仍 FAIL → 根因复盘**: 不再只 STOP, 而是走 `skein-check` 的根因复盘协议 (`references/root-cause-protocol.md`) 做跨维度结构化定位 — 从**需求 / 设计 / 实现 / 环境 / 测试** 5 维定位真正根因 + 给预防措施。出口二选一: ① 带根因回 exec 定向重修; ② STOP 并附根因报告转人工。可复用的教训回流 `skein-memory` sediment (踩坑留痕)。

### ⑥ finish (main 同步)

check 通过 → **sediment 判定门** (见下) → `skein.py finish`:

1. worktree 内 `git add -A` + commit (auto_commit=true 时)。
2. `git merge --no-ff skein/<id>` 合并回主工作区。冲突 → 自动 abort + 报冲突文件, **禁强解**。
3. 销 worktree + 删分支。
4. task → `completed`, 归档到 `.skein/task/archive/<年>/<月-日>/<id>/`。
5. focus 自动切到剩余首个 active task (若有)。

> finish 摘要可选 `skein.py journal --add "<本 task 完成情况>"` 记一笔 (append-only 过程日志, 随 task 一并归档; 无审批门, 区别 sediment 的判定门与 contract 的锁定)。

> finish 前 MUST 清理本 task 的悬挂 subagent / 后台任务 (`TaskList` 查 / `TaskStop` 关)。未关 = 未闭环, 禁宣告 Done。

## 双层动态 DAG 调度

两层**同构** — 同一套 DAG 算法, 只是调度对象不同:

| 层 | 调度对象 | 上限 |
| --- | --- | --- |
| **subtask 级** | 单 task 内的 subtask (派 `skein-implementer`) | 并发 2 |
| **task 级** | 同 session 多个 active task | active 集 ≤ 2 |

**DAG 边怎么来**: 最终 DAG = **冲突自算边** ∪ **显式 `depends_on` 边**。

- **冲突自算边**: 两个工作单元的写文件 glob 相交 / 执行范围相交 → 串行 (不能并行)。不相交 → 可并行。
- **显式 depends_on**: task.json 顶层 `deps` 字段 (`skein.py create --deps "t01,t02"`)。被依赖者未完成前, 依赖者不 ready。

**调度循环**: ready (前置全完成 + 无冲突占用) 即派 → 任一返回即查新 ready 立即派 → 并发始终 ≤ 2。exec 阶段 subtask 之间**禁停下问你顺序** (顺序归 planning 定; planning 没定就退回 planning 补, 不在 exec 问)。

多 task 并行细则见 [reference.md](reference.md) 的调度算法段, 或 skill `skein-flow/references/scheduling-algorithm.md`。

## 两层规则记忆 (差异化核心)

不同于 spec 式「按需沉淀单一文件」, SKEIN 记忆分两层, 存在 `.skein/spec/`:

| 层 | 路径 | 注入时机 | 适合 |
| --- | --- | --- | --- |
| **core** | `.skein/spec/core/<类目>/*.md` | 每 session 开始**自动常驻**注入 (SessionStart hook) | 「后续同类任务必再踩」的强约束 / 命令式契约 |
| **recall** | `.skein/spec/recall/<类目>/*.md` | 按任务语义**按需**召回 (planning 阶段 `recall <query>`) | 长尾、上下文密集的经验, 不占常驻预算 |

- **两层 × 类目**: 层内按类目 (git / test / arch / build / style / domain / ops...) 分子目录, 自由取名按需建。
- **三份索引**: 每层 `<layer>/index.md` + 顶层 `index.md` (两层聚合), sediment 写盘后自动 reindex。
- **core 预算警戒**: core 常驻注入有字符预算, 超了会警告「考虑降级部分到 recall」, 避免常驻上下文过重。

### bootstrap 冷启动播种 (一次性)

仓库**首次接入** SKEIN、`.skein/spec` 为空 / 近空时, 规则库没有历史经验可召回。此时 main 用 AskUserQuestion 征得同意后, 走 `skein-memory` 的冷启动播种 (`references/bootstrap-seeding.md`):

1. 派 `skein-researcher` (**bootstrap 扫描模式**) 扫既有代码库约定 — 命名 / 错误处理 / 测试 / 架构边界 / 构建 5 个维度, 提炼候选规则。
2. 逐条判 `core` / `recall` / `drop`, 经现有 sediment 审批门落盘。
3. **默认多归 recall** (静态扫描是推断而非踩坑实证), 仅「违反必炸」的硬约束才进 core。

这是**一次性动作** (仅冷启动跑一次), 后续增量经验仍走正常 finish sediment 累积。

### sediment 判定门 (finish 前必做)

每个 task finish 前, main 按 checklist 判本次 learning 该去哪:

| 判定 | 去向 |
| --- | --- |
| 新命令式契约 (MUST / 禁, 后续必再踩) | → **core** |
| 跨任务可复用经验但长尾 (选型 / 架构边界 / 踩坑根因) | → **recall** |
| 一次性 bug / 本 task 私有细节 / 已有规则覆盖 | → **drop** (不沉淀) |

判定归 model 语义判断 (脚本做不了), 全无增量则跳过, **禁硬凑沉淀**。写盘经 `memory.py sediment` (审批后), 自动 reindex。

## 工作区布局

```
.skein/
├── task.md                          # 看板 (skein.py board 渲染, 禁直接编辑)
├── state.json                       # {focus: <当前 task id>}
├── config.json                      # {max_active, auto_commit, worktree_root}
└── task/
    ├── <id>/                        # 活跃 task: prd.md / design.md / implement.md / task.json
    │   └── research/<topic>.md      # researcher 落盘的调研结论 (随 task finish 一并归档)
    └── archive/<年>/<月-日>/<id>/    # 按完成日期分层归档
.skein/spec/
├── index.md                         # 顶层索引 (两层聚合概览)
├── core/{<类目>/*.md, index.md}     # 常驻规则 + 层索引
└── recall/{<类目>/*.md, index.md}   # 按需召回规则 + 层索引
.worktrees/
└── skein-<id>/                      # task 隔离 worktree (finish 后销)
```

> SKEIN 自包含: `skein.py` 自身即引擎, `config.json` 是纯设置 (无外部生命周期 hook 层), start/finish 直接干活。

## 护栏机制

| 护栏 | 怎么实现 | 挡住什么 |
| --- | --- | --- |
| task.md 只读 | guard-skein.py PreToolUse hook (Edit/Write/MultiEdit → exit 2) | 手改看板导致格式漂移 |
| state.json 读写全挡 | 同 hook (Read/Edit/Write 全 block) | 绕过 skein.py 操作状态 |
| Recursion Guard | 3 个执行 agent 无 Agent/Task 工具 | subagent 自派 → 递归爆炸 |
| worktree 隔离 | 有 task 必有 worktree | 主工作区被半成品污染 |
| 闭环不可跳步 | 未 archive = 未完成 | 活儿做一半就宣告 Done |
| 契约不变量锁定 | planning 锁 `contracts`, check 逐条验 | 不变量在 exec 中被悄悄破坏 |
| compaction 永续 | `skein.py session-context` SessionStart hook 重注入活跃 task | 上下文压缩后忘掉在跑的 task |
