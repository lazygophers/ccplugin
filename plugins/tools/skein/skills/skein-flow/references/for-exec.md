# for-exec — exec 阶段作业手册

只管执行编排 (职责划分 / 并行 / 依赖), 不碰需求 / 方案设计 (那归 plan)。

## 触发与前置硬门

- **触发**: SKILL.md 参数路由 `$1=exec` (驱动就绪/在途 task 走完整闭环到 finish) 或 `$1` 缺省/flow (plan 收敛后自动续)。
- **入口硬门 = task 级状态先行** — 未 `skein start` (占槽建 worktree) 禁进 exec 调度门, 详见 [state-before-action.md](state-before-action.md) 硬门 1。
- **出口硬门 = subtask 全 done** — 全部 subtask done 才自动收束进 check, 半途禁跨阶段推进。

## 流程步骤

### 入口路由 (作命令时)

- **有入参 `<task-id>`** → 把请求**强制作为 SKEIN task 处理** (不 inline, 即使看似简单), 调用即「建 task 同意」。判新旧 → 加载 plan 阶段走完整闭环。
- **无入参 (空)** → 不建新 task, **驱动 `.skein` 内既有 task 走完整闭环直到 finish** (不止 exec):
  1. `skein list --status open --json`: 每项 `{id,status,name,desc,deps,worktree,pct,subs:[done,run,pend,fail],ready}` — `status=进行中/检查中` 即在途 active, `status=就绪 && ready=true` 即可启动; `status=待处理` = 规划中 (未过 `skein confirm`, 尚未就绪, 不可 start)。
  2. 无就绪、无在途 active → 报「无待执行 task」结束。
  3. 有 → 逐个走完整闭环 (task 级并发受 `max_active` 默认 2 限):
     - **就绪 task** → `skein start` (占 active 槽 + 建 worktree, 就绪→进行中) → 进 exec 调度门
     - **在途 进行中 task** → 直接进 exec 调度门续跑
     - task **全 subtask done → 自动进 check** → **check 全绿 → finish**
  4. **每个 task 必须走到 finish 才算完成**, 不止于 subtask 全 done。
- **前置**: 无 `.skein/` → 先 `skein init` 再继续。

### 调度门 (载体分工)

> **工作目录 (worktree 态自适应)** — 详见 [worktree-convention.md](worktree-convention.md)。真值一律以 task 的 `worktree` 字段为准 (null=原地)。

main 作调度器编排, 改动落各 subtask 工作目录、每个 agent 完成即回传:

- **🛑 subtask 状态先行 (硬前置)** — 详见 [state-before-action.md](state-before-action.md) 硬门 2。claim 占槽是派 agent 的硬前置, pending/failed 态 subtask 禁直接派 agent。
- **claim 默认即改态占槽 (整批标 running), 无需额外参数; --dry-run 才只读预览**。**调度** → main 亲跑: `skein claim` (**全局跨 task**, 所有 active task ready subtask 合池竞争同一 `max_active` 槽) 算就绪批 + 标 running, main 逐个真实 `Agent` 调用 dispatch。批量推进用 `claim`; 单 task 场景用 `skein subtask claim <tid>` 兼容; 预览用 `skein claim --dry-run`。
- **执行** → 派合适 agent (无则 `skein-executor`) 各做 1 subtask, 共享该 task 工作目录, 不调度不递归 (Recursion Guard)。
- **禁 main 亲改源码** — 实质产出一律派 subagent (仅上下文密集决策 / 用户显式要求等特别情况例外, 且必在该 task 工作目录内)。
- **载体 = 单 subagent (禁 team)** — agent-teams 已被 SessionStart 关闭, 需多 agent 协同的活一律拆成独立 subtask 各派单 subagent。
- **及早退出** — 每个载体只做本 subtask、产出即回传**立即退出**, 禁滞留空转。main 侧 `done` 后即 `claim` 放行下游, 全部 done 立即收束进 check。

### 调度循环 (动态, 完成即派)

调度循环本身 (`while skein claim 返回非空: 派 → 等回传 → done/fail → 再 claim`) 与并发上限 / 并行判定详见 [dag-scheduling.md](dag-scheduling.md) 第 5.1 节, 禁另抄一份。

- **🟢 subtask 调度优先, 空闲才提前 plan (禁干等)** — 详见 [dag-scheduling.md](dag-scheduling.md) 第 6 节 (plan-ahead)。优先级: 有可调度 subtask → 一律先 `claim` 派 subtask, plan-ahead 是次级填充器必须让位 subtask。
- **🔴 exec 无验收 (完成即 done, 验收全归 check)** — subagent 回传即执行完成, main **只 `done`/`fail`, 禁 exec 阶段勾验收**。exec 只判「执行有没有跑完/报错」, 不判「验收过没过」。
- **并行只看 depends_on DAG / 并发上限 2 / 完成即派** — 详见 [dag-scheduling.md](dag-scheduling.md)。任一返回即 `done` 后再 `claim`, 不等一批跑完。
- **返回 `需要:` / 阻塞 → 不计 done** — 该 subtask 未完成, 下游保持未 ready; main 转达用户/补信息后重派。
- **🔴 tight feedback loop (先复现再修, ask-matt 同源)** — subtask 失败/报错, **禁直接盲改**: 先建**一条就红的复现命令/最小测试**固定症状, 再读根因修。无复现 = 修了也无法验证, 是猜。自愈重派前 dispatch prompt MUST 含「先复现」指令。
- **subtask 失败 → 自愈闭环 (禁失败即停摆)** — 详见 [dag-scheduling.md](dag-scheduling.md) 第 7 节及 [subtask-operations.md](subtask-operations.md) 第 3 节, 禁另抄一份。二选一 (均在本 task scope 内): ① 定点小缺陷 → 原地重派 ≤2 轮; ② 根因是独立可修单元 → 插修复 subtask 定点修根因后重派。兜底: 修复也失败/累计无进展超上限/根因超 scope → 停回传 (走 root-cause-protocol 或转人工)。禁跳过该 subtask 放行下游。
- **exec 中发现独立新问题 → 自主拆新 task, 禁扩当前 scope** — 与自愈**互斥分流**: 自愈修的是**本 task scope 内**失败的 subtask; 本条是暴露**超出本 task 边界**的问题, main 自主走 plan 阶段 / `skein create` 登记为**新排队 task**, 禁塞进当前 task 扩范围。判据: 修复动作是否属原 subtask 目标 —— 属 → 自愈; 不属 → 拆新 task。

### ⚠️ exec 两条硬规

- **异步等待 MUST 输出任务清单** — 派出异步任务后、结束本回合前, 输出全景表: 4 列 id/状态/摘要/进度% (状态枚举 进行中/等待中/阻塞), 例 `| st1 | 进行中 | 改 auth 中间件 | 60 |`。同步前台阻塞 / 无在跑任务不触发。
- **exec 阶段禁问用户顺序** — 顺序归 planning (task.json 子任务 DAG + depends_on)。task.json 缺子任务 DAG → 退回 planning 补, **不在 exec 问**。

## 完成判据

- [ ] 每 ready subtask 均已派真实 `Agent` 或已 done/fail (无遗漏挂起)
- [ ] `claim` 返回空且无 depends_on 死锁 (确认无可调度项)
- [ ] 全部 subtask done → 已自动进 check (不止于 subtask 全 done 就停手)
- [ ] 回合末已输出任务清单 (有异步在跑时)

## 失败模式

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| subtask 报错 (非阻塞) | 自愈: 定点重派 ≤2 轮 / 根因独立则插修复 subtask | 修复也失败/超 scope → 停调度回传 main (走 root-cause-protocol), 禁跳过下游 |
| subagent 返回 `需要:` | main 转达用户 / 补信息后重派 | 信息仍缺 → 该 subtask 挂起, 下游保持未 ready, 禁标 done |
| `claim` 返回空 (满槽 / 无就绪) | 找 `待处理` 且无 subtask 的 task 提前 plan 填空闲 | 满槽等回传; 全 pending 有 subtask 但 `claim` 仍空 → 查 depends_on 死锁 (环) → 停手回 plan 改 DAG |

## 延伸引用

- [dag-scheduling.md](dag-scheduling.md) — 调度循环 / 并发上限 / plan-ahead / 自愈逻辑权威定义
- [subtask-operations.md](subtask-operations.md) — 自愈修复 subtask 操作规范 (第 3 节)
- [state-before-action.md](state-before-action.md) — task/subtask/check 三层状态先行硬门
- [worktree-convention.md](worktree-convention.md) — 工作目录约定 (worktree 态自适应)
- [root-cause-protocol.md](root-cause-protocol.md) — 根因复盘协议
