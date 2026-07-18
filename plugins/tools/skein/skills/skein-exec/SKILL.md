---
name: skein-exec
description: task exec 阶段执行编排调度门 + /skein-exec 闭环入口。作命令: 有入参→强制建 task 走闭环 (委托 skein-flow: plan→exec→check→finish, 不 inline); 无入参→驱动 .skein 既有 ready/active task 各走闭环。作 skill: 被 skein-flow exec 委托, main 按 depends_on DAG 为每个 subtask 选合适 agent 各执行 1 个, 改动落 task worktree。回传各 subtask 产物 / 需要 / 失败。硬约束: 并发上限 2、完成即派、main 禁亲改源码、载体单 subagent 不递归、异步等待 MUST 输出任务清单
user-invocable: true
argument-hint: "[task-id]"
arguments: "[task-id]"
model: haiku
effort: low
---

# skein-exec — 任务闭环入口 + 执行编排调度门

## 入口路由 (作 `/skein-exec` 命令时)

- **有入参 `<task-id>`** → 把请求**强制作为 SKEIN task 处理** (不 inline, 即使看似简单), 调用即「建 task 同意」。判新旧: 全新→新建 / 补充现有 active→并入 (裁定不准用 `AskUserQuestion`) → 加载 `skein-flow` 走**完整闭环** (plan→exec→check→finish, flow 承载, 本 skill 不复制)。
- **无入参 (空)** → 不建新 task, **驱动 `.skein` 内既有 task 走闭环**:
  1. `skein list --status open --json` (**一次取全部未完成 task 的压缩 JSON, 省 token**): 每项 `{id,status,name,desc,deps,worktree,pct,subs:[done,run,pend,fail],ready}` — `status=进行中/检查中` 即 active, `status=待处理 && ready=true` 即就绪批 (可 start)。不再分别跑 `ready`/`current`/直读 task.json。
  2. 无就绪 (无 `ready=true` 的 pending) 且无 active → 报「无待执行 task」结束。
  3. 有 → 对每个就绪/active task 加载 `skein-flow`: 已 planning 完成的从 exec 起 (直接下方调度门), 未 planning 的先补 plan。task 级并发上限 `max_active` (默认 2), ready 即派 / 完成即派 / 冲突或 `depends_on` 未满足则串行等。
  4. 全部 done → 报告完成。
- **前置**: 无 `.skein/` → 先 `skein init` 再继续。

> 下方是 exec 阶段**调度门本体** (被 `skein-flow` exec 委托, 或无入参驱动已 planning task 时进入)。**只管执行编排 (职责划分 / 并行 / 依赖), 不碰需求 / 方案设计 (那归 `skein-plan`)。**

## 调度门 (载体分工)

main 作调度器编排, 全部改动落 task worktree、主工作区零改动、每个 agent 完成即回传。角色分工:

- **调度** → main 亲跑 (脚本不能 spawn): `skein claim` (**全局跨 task**, 所有 active task ready subtask 合池竞争同一 `max_parallel` 槽) 算就绪批 + 标 running, main 逐个真实 `Agent` 调用 dispatch。批量推进用 `claim`; 单 task 场景用 `skein subtask claim <tid>` 兼容 (仅该 task 内截断); 只想先看一个可执行候选再决定是否执行, 用 `skein pop` (只读提取一个 (task, subtask) 对, 不改态)。
- **执行** → 派合适 agent (无则 `skein-executor`) 各做 1 subtask, 共享 task worktree, 不调度不递归 (Recursion Guard)。
- **禁 main 亲改源码** — 实质产出一律派 subagent (仅 ≤3 文件微改等特别情况例外, 且必在 task worktree 内)。
- **载体 = 单 subagent (禁 team)** — 每 subtask 派**单 subagent** (一次 `Agent` 调用); agent-teams 已被 skein SessionStart 关闭 (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=0`), 需多 agent 协同的活一律拆成独立 subtask 各派单 subagent, 不组 team。
- **及早退出** — 每个载体只做本 subtask、产出即回传**立即退出**, 禁滞留空转 / 轮询等待 / 揽额外活。main 侧 `done` 后即 `claim` 放行下游 (完成即派), 全部 done 立即收束进 check, 禁挂着不结。

## 调度循环 (动态, 完成即派)

```
while skein claim 返回非空:       # 全局跨 task: 所有 active task ready subtask 合池竞争 max_parallel 槽
    对认领到的每个 (task, subtask): 为其选合适 agent (无则 skein-executor) 真实 Agent 调用
    等任一 subagent 返回
    → skein subtask check/done/fail <tid> <sid> → 回到 skein claim (脚本自动重算就绪, 完成即派)
```
- 单 task 场景兼容: `skein subtask claim <tid>` (仅该 task 内截断, 不跨 task 竞争)。

- **并行只看 depends_on DAG** — ready = 所有前置 done + 有空闲并发槽。无写文件冲突自算 (发挥 AI 自主性: 有序关系靠 planning 写进 `depends_on`, 不靠脚本猜文件重叠)。
- **并发上限 2 / 完成即派** — 任一返回即 `done` 后再 `claim`, 脚本立刻放行新就绪, 不等一批跑完。
- **返回 `需要:` / 阻塞 → 不计 done** — 该 subtask 未完成, 下游保持未 ready; main 转达用户/补信息后重派, 禁标完成、禁放行下游。
- **subtask 失败 → 自愈闭环 (禁失败即停摆)** — subtask 报错/验收不过, main 读根因**自主修**, 二选一 (均在本 task scope 内): ① 定点小缺陷 → 缩范围**原地重派** `subtask start` (≤2 轮); ② 根因是独立可修单元 → **自主 `subtask add --deps` 插修复 subtask** 定点修根因 → 修复 done 后重派失败 subtask。兜底: 修复也失败/累计无进展超上限/根因超 scope → 停回传 (走 skein-check root-cause-protocol 或转人工)。禁跳过该 subtask 放行下游。详见 [scheduling-algorithm.md](references/scheduling-algorithm.md)。
- **exec 中发现独立新问题 → 自主拆新 task, 禁扩当前 scope** — 与上条自愈**互斥分流**: 自愈修的是**本 task scope 内**失败的 subtask (完成原范围); 本条是 subagent 回传暴露**超出本 task 边界**的问题 (新缺陷 / 新需求 / 需单独验收的关联改动), main 自主走 `skein-plan` / `skein create` 登记为**新排队 task** (与当前 task 有先后用 `--deps` 连边, 无则并行; active 集 ≤ 2 自动排队), 禁塞进当前 task 扩范围。当前 task 按原 scope 收束。判据: 修复动作是否属原 subtask 目标 —— 属 → 自愈 (加修复 subtask); 不属 → 拆新 task。

## ⚠️ 两条硬规

- **异步等待 MUST 输出任务清单** — 派出异步任务后、结束本回合前, 输出全景表 (4 列 id/状态/摘要/进度%, 状态枚举 进行中/等待中/阻塞)。格式见 [references/progress-reporting.md](references/progress-reporting.md)。同步前台阻塞 / 无在跑任务不触发。
- **exec 阶段禁问用户顺序** — 顺序归 planning (task.json 的子任务 DAG + depends_on)。exec 只跑动态调度循环。task.json 缺子任务 DAG (depends_on) → 退回 planning 补, **不在 exec 问**。

## 调度算法 (双层同构 + dispatch prompt)

subtask 级 + 多 task 级两层同构 (同一套 DAG), subtask 状态经 `skein subtask` 脚本落盘, dispatch prompt 6 字段自包含 (含 Recursion Guard + 读后写硬门)。完整命令表 + 调度 DAG 定义 + worktree 规则 + 多 task 并行 + dispatch prompt 模板见 [references/scheduling-algorithm.md](references/scheduling-algorithm.md)。

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发                          | 一线修复                                   | 仍失败兜底                                       |
| ----------------------------- | ------------------------------------------ | ------------------------------------------------ |
| subtask 报错 (非阻塞)         | 自愈: 定点小缺陷原地重派 ≤2 轮 / 根因独立则 `subtask add --deps` 插修复 subtask 定点修后重派失败 subtask | 修复也失败/累计无进展超上限/超 scope → 停调度回传 main (走 root-cause-protocol), 禁跳过下游 |
| subagent 返回 `需要:`         | main 转达用户 / 补信息后重派该 subtask     | 信息仍缺 → 该 subtask 挂起, 下游保持未 ready, 禁标 done |
| `claim` 返回空但仍有 pending  | 查 depends_on 是否死锁 (环 / 前置永不 done) | 确为环 → 停手回 skein-plan 改 DAG, 禁空转轮询     |

## ❌ 反例 (命中=流程错误)

> 🔒 Iron Law: main 禁亲改源码 — 实质产出一律派 subagent (仅 ≤3 文件微改例外且必在 task worktree 内)。

违反上文即流程错误: main 亲改源码 (应派 subagent) / 一批跑完才派下一批 (应完成即派) / 并发超 2 / 标 `需要:` 的 subtask 计 done 放行下游 / 在 subtask 间停下问用户顺序 (顺序归 planning, task.json 缺子任务 DAG 退回 planning 补) / ❌ 派出异步任务后不输出任务清单 → ✅ 回合末输出 4 列全景表 (id/状态/摘要/进度%) / 用本 skill 做需求方案设计 (那归 skein-plan) / 组 subagent-team (已禁用, 一律拆 subtask 各派单 subagent) / 载体产出后滞留空转不退出 (应及早退出) / exec 中发现独立新问题却塞进当前 task 扩 scope (应自主拆新排队 task) / subtask 失败即停等人工不自愈 (应先自愈: 原地重派或加修复 subtask, 兜底才回传)。
