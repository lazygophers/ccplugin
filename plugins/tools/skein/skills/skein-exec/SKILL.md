---
name: skein-exec
description: task exec 阶段执行编排调度。planning 产物齐、start 后使用 (被 skein-flow exec 委托, 也可 /skein-exec 单独续跑已规划 task) — main 作调度器按 depends_on DAG 为每个 subtask 选合适 agent 各执行 1 个, ready 即派 / 完成即派 / 并发上限 2, 改动落 task worktree。含双层 (subtask 级 + 多 task 级) 同构调度算法 + 异步任务清单
user-invocable: true
argument-hint: "[task_id]"
arguments: "[task_id]"
model: opus
effort: high
---

# skein-exec — 执行编排调度门

exec 阶段的**调度器**。main 作调度器, 动态 DAG 为每个 subtask 选合适 agent (按任务性质挑现有 agent, 无合适的用 `skein-executor`) 各执行 1 subtask, 全部改动落 task worktree, 主工作区零改动。每个 agent 完成即回传。**只管执行编排 (职责划分 / 并行 / 依赖), 不碰需求 / 方案设计 (那归 `skein-plan`)。**

## 载体

- **调度** → main 亲跑 (脚本不能 spawn): `skein.py subtask claim` 算就绪批 + 标 running, main 逐个真实 `Agent` 调用 dispatch。
- **执行** → 派合适 agent (无则 `skein-executor`) 各做 1 subtask, 共享 task worktree, 不调度不递归 (Recursion Guard)。
- **禁 main 亲改源码** — 实质产出一律派 subagent (仅 ≤3 文件微改等特别情况例外, 且必在 task worktree 内)。

## 调度循环 (动态, 完成即派)

```
while skein.py subtask claim <tid> 返回非空:       # 脚本一步: 算就绪 + 标 running (≤ max_parallel)
    对认领到的每个 subtask: 为其选合适 agent (无则 skein-executor) 真实 Agent 调用
    等任一 subagent 返回
    → subtask check/done/fail <sid> → 回到 claim (脚本自动重算就绪, 完成即派)
```

- **并行只看 depends_on DAG** — ready = 所有前置 done + 有空闲并发槽。无写文件冲突自算 (发挥 AI 自主性: 有序关系靠 planning 写进 `depends_on`, 不靠脚本猜文件重叠)。
- **并发上限 2 / 完成即派** — 任一返回即 `done` 后再 `claim`, 脚本立刻放行新就绪, 不等一批跑完。
- **返回 `需要:` / 阻塞 → 不计 done** — 该 subtask 未完成, 下游保持未 ready; main 转达用户/补信息后重派, 禁标完成、禁放行下游。
- **subtask 报错 → 不推进** — 按 dispatch 失败处理缩范围重试; 反复失败 → 停并回传, 禁跳过继续。

## 两条硬规

- **异步等待 MUST 输出任务清单** — 派出异步任务后、结束本回合前, 输出全景表 (4 列 id/状态/摘要/进度%, 状态枚举 进行中/等待中/阻塞)。格式见 [references/progress-reporting.md](references/progress-reporting.md)。同步前台阻塞 / 无在跑任务不触发。
- **exec 阶段禁问用户顺序** — 顺序归 planning (调度图 + depends_on DAG)。exec 只跑动态调度循环。PRD 缺调度图 → 退回 planning 补, **不在 exec 问**。

## 调度算法 (双层同构 + dispatch prompt)

subtask 级 + 多 task 级两层同构 (同一套 DAG), subtask 状态经 `skein.py subtask` 脚本落盘, dispatch prompt 6 字段自包含 (含 Recursion Guard + 读后写硬门)。完整命令表 + 调度 DAG 定义 + worktree 规则 + 多 task 并行 + dispatch prompt 模板见 [references/scheduling-algorithm.md](references/scheduling-algorithm.md)。

## 反例

违反上文即流程错误: main 亲改源码 (应派 subagent) / 一批跑完才派下一批 (应完成即派) / 并发超 2 / 标 `需要:` 的 subtask 计 done 放行下游 / 在 subtask 间停下问用户顺序 (顺序归 planning, PRD 缺调度图退回 planning 补) / 派出异步任务后不输出任务清单 / 用本 skill 做需求方案设计 (那归 skein-plan)。
