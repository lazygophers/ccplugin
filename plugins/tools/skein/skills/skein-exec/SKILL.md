---
name: skein-exec
description: SKEIN task 闭环入口 + exec 调度门。作 /skein-exec 命令: 有入参→请求强制作 task 走闭环 (委托 skein-flow: plan→exec→check→finish, 不 inline); 无入参→驱动 .skein 既有 ready/active task 各走闭环 (task 级并发 2)。作 skill: 被 skein-flow exec 委托, main 作调度器按 depends_on DAG 为每个 subtask 选合适 agent 各执行 1 个, ready 即派 / 完成即派 / 并发上限 2, 改动落 task worktree。含双层 (subtask 级 + 多 task 级) 同构调度算法 + 异步任务清单
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
  1. `skein.py list --status open --json` (**一次取全部未完成 task 的压缩 JSON, 省 token**): 每项 `{id,status,name,desc,deps,worktree,pct,subs:[done,run,pend,fail],ready}` — `status=进行中/检查中` 即 active, `status=待处理 && ready=true` 即就绪批 (可 start)。不再分别跑 `ready`/`current`/直读 task.json。
  2. 无就绪 (无 `ready=true` 的 pending) 且无 active → 报「无待执行 task」结束。
  3. 有 → 对每个就绪/active task 加载 `skein-flow`: 已 planning 完成的从 exec 起 (直接下方调度门), 未 planning 的先补 plan。task 级并发上限 `max_active` (默认 2), ready 即派 / 完成即派 / 冲突或 `depends_on` 未满足则串行等。
  4. 全部 done → 报告完成。
- **前置**: 无 `.skein/` → 先 `skein.py init` 再继续。

> 下方是 exec 阶段**调度门本体** (被 `skein-flow` exec 委托, 或无入参驱动已 planning task 时进入)。**只管执行编排 (职责划分 / 并行 / 依赖), 不碰需求 / 方案设计 (那归 `skein-plan`)。**

## 调度门 (载体分工)

main 作调度器编排, 全部改动落 task worktree、主工作区零改动、每个 agent 完成即回传。角色分工:

- **调度** → main 亲跑 (脚本不能 spawn): `skein.py subtask claim <tid>` 算就绪批 + 标 running, main 逐个真实 `Agent` 调用 dispatch。批量推进用 `claim`; 只想先看一个可执行候选再决定是否执行, 用 `skein.py pop` (只读提取一个 (task, subtask) 对, 不改态)。
- **执行** → 派合适 agent (无则 `skein-executor`) 各做 1 subtask, 共享 task worktree, 不调度不递归 (Recursion Guard)。
- **禁 main 亲改源码** — 实质产出一律派 subagent (仅 ≤3 文件微改等特别情况例外, 且必在 task worktree 内)。
- **载体优先 subagent, 非必要不用 team** — 单 subtask 优先派**单 subagent** (一次 `Agent` 调用); 仅真正需多 agent 协同同一产物时才用 subagent-team, 能拆成独立 subtask 就拆开各派单 subagent。
- **及早退出 (subagent / team / workflow 皆适用)** — 每个载体只做本 subtask、产出即回传**立即退出**, 禁滞留空转 / 轮询等待 / 揽额外活。main 侧 `done` 后即 `claim` 放行下游 (完成即派), 全部 done 立即收束进 check, 禁挂着不结。

## 调度循环 (动态, 完成即派)

```
while skein.py subtask claim <tid> 返回非空:       # 脚本一步: 算就绪 + 标 running (≤ max_parallel)
    对认领到的每个 subtask: 为其选合适 agent (无则 skein-executor) 真实 Agent 调用
    等任一 subagent 返回
    → skein.py subtask check/done/fail <tid> <sid> → 回到 claim (脚本自动重算就绪, 完成即派)
```

- **并行只看 depends_on DAG** — ready = 所有前置 done + 有空闲并发槽。无写文件冲突自算 (发挥 AI 自主性: 有序关系靠 planning 写进 `depends_on`, 不靠脚本猜文件重叠)。
- **并发上限 2 / 完成即派** — 任一返回即 `done` 后再 `claim`, 脚本立刻放行新就绪, 不等一批跑完。
- **返回 `需要:` / 阻塞 → 不计 done** — 该 subtask 未完成, 下游保持未 ready; main 转达用户/补信息后重派, 禁标完成、禁放行下游。
- **subtask 报错 → 不推进** — 按 dispatch 失败处理缩范围重试; 反复失败 → 停并回传, 禁跳过继续。

## 两条硬规

- **异步等待 MUST 输出任务清单** — 派出异步任务后、结束本回合前, 输出全景表 (4 列 id/状态/摘要/进度%, 状态枚举 进行中/等待中/阻塞)。格式见 [references/progress-reporting.md](references/progress-reporting.md)。同步前台阻塞 / 无在跑任务不触发。
- **exec 阶段禁问用户顺序** — 顺序归 planning (task.json 的子任务 DAG + depends_on)。exec 只跑动态调度循环。task.json 缺子任务 DAG (depends_on) → 退回 planning 补, **不在 exec 问**。

## 调度算法 (双层同构 + dispatch prompt)

subtask 级 + 多 task 级两层同构 (同一套 DAG), subtask 状态经 `skein.py subtask` 脚本落盘, dispatch prompt 6 字段自包含 (含 Recursion Guard + 读后写硬门)。完整命令表 + 调度 DAG 定义 + worktree 规则 + 多 task 并行 + dispatch prompt 模板见 [references/scheduling-algorithm.md](references/scheduling-algorithm.md)。

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发                          | 一线修复                                   | 仍失败兜底                                       |
| ----------------------------- | ------------------------------------------ | ------------------------------------------------ |
| subtask 报错 (非阻塞)         | 按 dispatch 失败处理缩范围重试 1 次        | 反复失败 → 停调度回传 main, 禁跳过继续下游       |
| subagent 返回 `需要:`         | main 转达用户 / 补信息后重派该 subtask     | 信息仍缺 → 该 subtask 挂起, 下游保持未 ready, 禁标 done |
| `claim` 返回空但仍有 pending  | 查 depends_on 是否死锁 (环 / 前置永不 done) | 确为环 → 停手回 skein-plan 改 DAG, 禁空转轮询     |

## 反例

违反上文即流程错误: main 亲改源码 (应派 subagent) / 一批跑完才派下一批 (应完成即派) / 并发超 2 / 标 `需要:` 的 subtask 计 done 放行下游 / 在 subtask 间停下问用户顺序 (顺序归 planning, task.json 缺子任务 DAG 退回 planning 补) / 派出异步任务后不输出任务清单 / 用本 skill 做需求方案设计 (那归 skein-plan) / 单 subtask 硬上 subagent-team (应优先单 subagent) / 载体产出后滞留空转不退出 (应及早退出)。
