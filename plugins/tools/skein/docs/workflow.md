# 运行机制

本篇讲 SKEIN 内部怎么转: 谁在调度、任务怎么闭环、并行怎么调、记忆怎么沉淀。

## 角色分工

| 角色 | 是谁 | 干什么 | 有 Agent/Task 工具? |
| --- | --- | --- | --- |
| **main** | 主对话 (coordinator) | 调度器: 跑 `skein.py` 脚本、派 subagent、与你交互决策、回传进度、维护看板 | 有 (能派) |
| **执行者** | main 选的合适 agent (无则 `general-purpose`) | worktree 内执行 **1 个** subtask, 写代码 | 有 (递归护栏靠 dispatch prompt 硬性禁止再派) |
| **skein-checker** | 验证 agent (绑 `skein-check`) | 只读, 跑 lint / type / test / 契约校验 + subtask 产物一致性核查 (报冲突对) | 无 |
| **skein-researcher** | 调研 agent | planning 纯信息调研 (选型 / 对比); **bootstrap 扫描模式** 扫既有代码库约定提炼候选规则, 结论落盘 `research/` | 无 |
| **skein-finisher** | 收尾勘察 agent (绑 `skein-finish`) | 只读, finish 前扫悬挂 subagent/后台任务 + 核 check 全绿 + 查未提交遗漏 | 无 |
| **skein-memorier** | 记忆员 agent (绑 `skein-memory`) | 只读, recall 检索 (planning) + sediment 草案 (finish 读 journal+diff 跑判定门产 core/recall/drop 候选) | 无 |

**铁律**: main 默认**不亲自写源码** — 实质产出派 subagent。执行 subtask 由 main 按性质选合适 agent (无则 `general-purpose`), 其递归护栏靠 dispatch prompt 硬性禁止再派 subagent (自己动手做完 1 个 subtask)。验证 / 调研 / 收尾 / 记忆的 4 个具名 agent (checker / researcher / finisher / memorier) **没有** Agent/Task 工具兜住递归, 各自只干一件事; checker / finisher / memorier 各与对应 skill 相互绑定 (frontmatter `skills:`)。

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
- 产出: `prd.md` (主入口) + `design.md` (详细设计) + 需调研时 `findings.md` (调研收敛); 子任务 + 调度 DAG 经 `skein.py subtask add` 落 task.json。请你评审 (AskUserQuestion)。

### ② memory recall (main 委托 `skein-memorier`)

派 `skein-memorier` 按任务描述从 `recall` 层召回相关规则, 命中条目注入各 dispatch prompt「已知」段 (`core` 规则 session 开始只注入**极简索引**, 全文按需 `memory.py inject-core` 拉)。让本 task 带上项目历史经验。这是**全流程记忆闭环**的召回端 (沉淀端见 ⑥ finish sediment)。

### ③ 激活 (main 同步)

grill 通过 + 你评审确认 → `skein.py start`:

- 建 git worktree: `git worktree add -b skein/<id> .worktrees/skein-<id> HEAD`
- task 状态 → `in_progress`, 写入 worktree 路径。无 task 级 focus — 就绪 task 皆可并行。
- 检查前置 (`deps`) 都完成、active 集未超上限 2。

### ④ exec (main 调度 + subagent 执行)

main 作调度器跑**动态 DAG 调度循环**:

- 读 task.json 的 `subtasks[]` (planning 已用 `subtask add` 登记), 按显式 `depends_on` 组成 DAG (并行只看这张 DAG, 无写文件冲突自算)。
- **ready 即派** — 为每个 subtask 选合适 agent (无则 `general-purpose`), 6 字段自包含 prompt (携带执行纪律 + 递归护栏), **并发上限 2**, **完成即派**下一个 (不空等全部)。
- **读后写硬门 + 验收标准自检**: 改哪些文件由执行 agent 在 worktree 内**自主决定** (给自主权), 完成前对照 planning 登记的**验收标准 checklist** 逐条自检。执行 agent 收 subtask 后, 对每个待改文件必过 **写前 CHECKPOINT**: 先 `Read` 全文 → 复述适用契约 (只复述契约, 不含 reason) → 才 `Edit`/`Write`; 若文件现状与契约矛盾, 标 `需要:` 回传, **不擅改**。此硬门经 dispatch prompt 携带 (无论选中哪个 agent 都照做); 契约约束从 check 事后验**前移到写前** (契约仍是 planning 锁进 task.json 的同一份, 不重造)。
- 所有改动落 task worktree, 主工作区零改动。
- 每个 agent 完成 / 阻塞 → main **立即**回传摘要 (禁批量延迟)。
- 派出异步任务后结束本回合前, MUST 输出任务全景表 (状态: 进行中 / 等待中 / 阻塞)。

### ⑤ check (main 派 checker fan-out)

派 `skein-checker` 验证 spec 合规 / lint / type / tests。checker 先 `skein.py contract <id>` 读出 planning 阶段锁定的契约, **逐条验证 pass/fail** (不变量守住没), 并做 **subtask 产物一致性核查** (接口签名对不上 / 重复实现同一职责 / 命名与约定相斥 / 数据流断裂 / 契约互相矛盾, 逐条报冲突对)。

**处置分两路** (关键): 
- **孤立失败** (单点 lint/type/test/契约 fail, 无跨 subtask 冲突) → **定点修复**: 派合适 agent (无则 `general-purpose`) 只改失败相关文件, 重检。
- **一致性冲突 或 check 失败根因跨 subtask** → 🔴 **深化拆分 (非定点补丁)**: 冲突根因在 planning 拆分不到位, 定点补丁治标。回 `skein.py plan` 把每个冲突根因拆成新 subtask (一冲突一 subtask, 逐条覆盖, 更新 DAG/契约), 重跑 exec→check。**直到全绿且零冲突才放行** — 未覆盖完所有冲突禁 finish。

**第 3 轮仍 FAIL → 根因复盘**: 不再只 STOP, 而是走 `skein-check` 的根因复盘协议 (`references/root-cause-protocol.md`) 做跨维度结构化定位 — 从**需求 / 设计 / 实现 / 环境 / 测试** 5 维定位真正根因 + 给预防措施。出口二选一: ① 带根因回 exec 定向重修; ② STOP 并附根因报告转人工。可复用的教训回流 `skein-memory` sediment (踩坑留痕)。

### ⑥ finish (main 委托 `skein-finish` 编排)

check 全绿后被 flow 委托给 `skein-finish` 收尾编排门, 顺序: **派 `skein-finisher` 收尾勘察 → 委托 `skein-memory` sediment (见下) → 清理悬挂 → `skein.py finish`**。

- **收尾勘察** (`skein-finisher`, 只读): 扫悬挂 subagent/后台任务 + 复核 check 全绿 + 查未提交遗漏, 回传勘察报告供 main 决定是否放行。
- **sediment 判定门** (委托 `skein-memory`): `skein-memorier` 读 journal+diff 跑判定门产候选 (core/recall/drop 分层草案) → main 逐项输出 trace + AskUserQuestion 审批 + `memory.py sediment` 写盘。无增量则跳过 (禁硬凑)。
- **`skein.py finish`** (main 同步):
  1. worktree 内 `git add -A` + commit (auto_commit=true 时)。
  2. `git merge --no-ff skein/<id>` 合并回主工作区。冲突 → 自动 abort + 报冲突文件, **禁强解**。
  3. 销 worktree + 删分支。
  4. task → `completed`, 归档到 `.skein/task/archive/<年>/<月-日>/<id>/`。
  5. 从顶层 tasks 索引移除 (其余 active task 不受影响, 继续并行)。

> finish 摘要可选 `skein.py journal --add "<本 task 完成情况>"` 记一笔 (append-only 过程日志, 随 task 一并归档; 无审批门, 区别 sediment 的判定门与 contract 的锁定)。

> finish 前 MUST 清理本 task 的悬挂 subagent / 后台任务 (`TaskList` 查 / `TaskStop` 关)。未关 = 未闭环, 禁宣告 Done。

## 双层动态 DAG 调度

两层**同构** — 同一套 DAG 算法, 只是调度对象不同:

| 层 | 调度对象 | 上限 |
| --- | --- | --- |
| **subtask 级** | 单 task 内的 subtask (为每个选合适 agent, 无则 `general-purpose`) | 并发 2 |
| **task 级** | 同 session 多个 active task | active 集 ≤ 2 |

**DAG 边怎么来**: **并行只看显式 `depends_on` DAG** (无写文件冲突自算 — 真正有序的关系靠 planning 写进 `depends_on`, 不靠脚本猜写文件重叠)。

- **subtask 级**: `subtask add --deps "s1,s2"` (存 `subtasks[].depends_on`)。被依赖者未 done 前, 依赖者不 ready; 无依赖者可并行。
- **task 级**: `create --deps "order-query,order-create-api"` (存 task.json `deps`)。各 active task 各占各 worktree, 只看 task.json `deps` 决定串并行。

**subtask 状态脚本落盘 (非肉眼看 md 文件)**: subtask DAG 存 per-task `task.json` 的 `subtasks[]`, 经 `skein.py subtask add/claim/done/fail` 维护, 渲染到 per-task `task.md`。**脚本一次性算就绪批 + 改态** (依赖 (`depends_on`) 全 done + 空闲槽 → 整批标 running), **只派 agent 归 main** (脚本不能 spawn):

```
拆好 → subtask add …               (逐个登记 sid/deps/check 验收标准)
  ┌── subtask claim <tid>          ← 脚本算就绪批 + 整批标 running (一步到位)
  │      ↓ 非空: 逐个为 subtask 选合适 agent (无则 general-purpose) 执行 (无需再 start)
  │      ↓ agent 回: subtask check --passed "1,3" (勾验收→百分比) → done/fail → 立即回传
  └──────┘  循环至 claim 恒空且无 running
```

**调度循环**: `claim` 认领即派 → 任一返回即 `check` 勾验收 (完成百分比 = 已过/总验收, 看板渲染进度条; `done` 自动标满 100%) + done/fail + 再 `claim` 立即派 → 并发始终 ≤ `max_parallel` (默认 2)。**脚本一步算+改态, main 不逐个 start** (少一轮往返, 无竞态窗口; `ready` 是只读预览, `start` 仅单个 retry 补派)。exec 阶段 subtask 之间**禁停下问你顺序** (顺序归 planning 定; planning 没定就退回 planning 补, 不在 exec 问)。

多 task 并行细则见 [reference.md](reference.md) 的调度算法段, 或 skill `skein-exec/references/scheduling-algorithm.md`。

## 两层规则记忆 (差异化核心)

不同于 spec 式「按需沉淀单一文件」, SKEIN 记忆分两层, 存在 `.skein/spec/`:

| 层 | 路径 | 注入时机 | 适合 |
| --- | --- | --- | --- |
| **core** | `.skein/spec/core/<类目>/*.md` | 每 session 开始注入**极简索引** (仅标题, SessionStart hook); 全文按需 `inject-core` 拉 | 「后续同类任务必再踩」的强约束 / 命令式契约 |
| **recall** | `.skein/spec/recall/<类目>/*.md` | 按任务语义**按需**召回 (planning 阶段 `recall <query>`) | 长尾、上下文密集的经验, 不占常驻预算 |

- **两层 × 类目**: 层内按类目 (git / test / arch / build / style / domain / ops...) 分子目录, 自由取名按需建。
- **三份索引**: 每层 `<layer>/index.md` + 顶层 `index.md` (两层聚合), sediment 写盘后自动 reindex。
- **core 预算警戒**: 全文有字符预算 (超了 sediment 提示降级到 recall); SessionStart **只注入极简索引** (每条一行标题) 并另有 token 硬预算守卫 (`hooklib`, 超则截断+告警) — 常驻上下文恒定小, 避免不可控膨胀, 全文按需 `inject-core`。

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

判定归 model 语义判断 (脚本做不了), 全无增量则跳过, **禁硬凑沉淀**。候选草案由 `skein-memorier` (读 journal+diff 跑判定门) 产出, 审批 (AskUserQuestion) + 写盘经 `memory.py sediment` 仍归 main, 自动 reindex。

## 工作区布局

```
.skein/
├── .gitignore                       # init 生成: 忽略 task.md (自动渲染)
├── task.json                        # 顶层 {tasks:[...]} 全表 — 脚本维护, AI 禁读写
├── task.md                          # 顶层看板 (task.json 渲染, git 忽略) — 脚本维护, AI 禁读写
├── config.yaml                      # max_active / max_parallel / auto_commit / worktree_root
└── task/
    ├── <id>/                        # 活跃 task
    │   ├── task.json                # 记录 + subtask DAG — 脚本维护, AI 禁读写
    │   ├── task.md                  # 子任务看板 (渲染, git 忽略) — 脚本维护, AI 禁读写
    │   ├── prd.md                   # 主入口: 需求 + 索引区 (AI 读写)
    │   ├── design.md                # 详细设计: 架构/取舍/选型, 不含调度图 (AI 读写)
    │   ├── findings.md              # 调研收敛结论 (AI 读写; 过程存 research/)
    │   ├── journal.md               # append-only 过程记录 (AI 追加, 随 task 归档)
    │   └── research/<topic>.md      # researcher 过程笔记 (最终收敛进 findings.md, 随 task finish 归档)
    └── archive/<年>/<月-日>/<id>/    # 按完成日期分层归档
.skein/spec/
├── index.md                         # 顶层索引 (两层聚合概览)
├── core/{<类目>/*.md, index.md}     # 常驻规则 + 层索引
└── recall/{<类目>/*.md, index.md}   # 按需召回规则 + 层索引
.worktrees/                          # init 追加到仓库根 .gitignore (worktree_root, 不入库)
└── skein-<id>/                      # task 隔离 worktree (finish 后销)
```

> SKEIN 自包含: `skein.py` 自身即引擎, `config.yaml` 是纯设置 (无外部生命周期 hook 层), start/finish 直接干活。

## 护栏机制

| 护栏 | 怎么实现 | 挡住什么 |
| --- | --- | --- |
| task.json/task.md 全挡 | guard-skein.py PreToolUse hook (顶层 + per-task, Read/Edit/Write 全 exit 2) | AI 绕过 skein.py 直接读写状态/看板 → 格式漂移或态不一致 |
| Recursion Guard | 具名 agent (checker/researcher) 无 Agent/Task 工具; 执行者 (general-purpose 等有 Agent/Task) 靠 dispatch prompt 硬性禁止再派 | subagent 自派 → 递归爆炸 |
| worktree 隔离 | git 仓库内: 有 task 必有 worktree (非 git 仓库降级原地执行) | 主工作区被半成品污染 |
| 闭环不可跳步 | 未 archive = 未完成 | 活儿做一半就宣告 Done |
| 契约不变量锁定 | planning 锁 `contracts`, check 逐条验 | 不变量在 exec 中被悄悄破坏 |
| compaction 永续 | `skein.py session-context` SessionStart hook 重注入活跃 task | 上下文压缩后忘掉在跑的 task |
| hook token 可控 | 所有注入过 `hooklib.budget_guard` (session-start 索引 + session-context); core 只注入极简索引 | 常驻上下文不可控膨胀 |
| .skein 操作免打断 | `allow-skein.py` PermissionRequest 对引擎命令 / prd 等工件默认同意 | 逐次授权拖慢闭环 (task.json/task.md 仍归 guard 硬阻) |
| 并发写竞态防护 | `batch-skein.py` PostToolBatch 拦同批 ≥2 个 .skein 状态写命令 | 并行写 task.json/spec 后写覆盖前写 |
| 脚本报错留痕 | `report-skein.py` PostToolUseFailure 注入错误上下文 + 引导手动报 issue | 插件 bug 被静默吞掉 |
