---
name: skein-flow
description: 强制 task 闭环。复杂/多步/跨文件请求, 或用户显式要求把请求作为 SKEIN task 处理时使用 — 强推 plan→exec→check→finish 全流程, main 作调度器派 subagent 在 worktree 内执行, 禁 inline 直接做
argument-hint: "[任务描述]"
arguments: "[任务描述]"
model: sonnet
effort: medium
---

把请求**强制作为 SKEIN task 处理**, 除非用户输入 `--skip`，否则禁 inline 直接做 (即使看似简单)。但**不等于一定新建** — 先判**全新任务** vs **对现有 active task 的补充**, 再决定新建/并入

## 执行载体铁律 (最高优先级)
「派 agent」=真实 `Agent` tool_use / main 默认禁写源码 / 有 task 必有 worktree / dispatch 6 字段 / 完成即时回传 / 并发请求禁互相顶掉 等。全量 11 条铁律详见 [references/carrier-rules.md](references/carrier-rules.md)。

## 任务执行流程 (plan → exec → check → finish 四步闭环)
### plan
- **先查未完成再 durable 登记 (防丢/防并发覆盖/防堆重复)** — 第一步先跑 `skein list --status open --json` 判归属: 相关 → 并入补 subtask 不新建; 无相关才 `skein create` 落 pending。被中断/顶掉亦可 `/skein-exec` 无参续跑, **绝不静默跳过**。**禁不查就 create、禁一直堆新 task**。
- **memory recall** — 派 `skein-specer` 召回 recall 规则注入 dispatch prompt「已知」段 (core 规则已常驻)。
- Skill(skein-grill) 确认需求 → Skill(skein-plan --continue) 规划+`subtask add` 登记 → 🛑 ToolCall(AskUserQuestion) 评审确认 → `skein start <id>` 激活 (建 worktree)。未确认禁进 exec (硬门 · STOP)。
### exec
- Skill(skein-exec) DAG 就绪即派 / 完成即派 (并发上限 2)。**执行一律派 agent (🛑 硬门)**: 有 subtask 走 `claim→派 Agent→done→claim`; 无 subtask main 派 1 个 `skein-executor`。**禁 main inline 顺跑**。派发后回合末 MUST 输出任务清单; 禁问顺序。
- **exec/check/finish 禁动 design.md** — 方案调整回 planning 改 design 后重派。
### check
- Agent(skein-checker) 跑 lint/type-check/tests/契约合规 + **一致性核查**。未过或检出冲突 → **回 planning 重确认 (task 保持 `进行中`)**: grill/AskUserQuestion 与用户**确认修复方向** (定点修/重拆/改契约), **禁跳过确认直接补 subtask**; 确认后同 task `subtask add` 修复子任务 (`--deps` 挂失败源) 回 exec 重派, 全绿且零冲突才放行。详见 `skein-check` skill。
### finish
- Skill(skein-finish) 收尾门 (check 全绿后): 派 `skein-finisher` 勘察 → 委托 `skein-spec` sediment → 清理悬挂 → `skein finish`。**sediment 判定门 (自动沉淀)**: `skein-specer` 产候选 → main 逐项 trace + `skein-spec sediment` 自动写盘; 无增量跳过。详见 `skein-finish` skill。

## 作用域边界 (何时建 task)

| 特征                              | 判定                         |
| --------------------------------- | ---------------------------- |
| 纯查询 / 文档阅读 / 问答 (无改动) | 豁免                         |
| 单文件单处改, ≤20 行且位置已知    | 豁免                         |
| 跨 ≥2 文件 / 单文件多处 / 多步骤  | **必建 task**                |
| 需外部调研 / 产出文档交付         | **必建 task**                |
| 边界模糊                          | **AskUserQuestion 用户裁定** |

归一 vs 分立 / worktree 豁免 / 完成判定 详见 [references/scope-boundary.md](references/scope-boundary.md)。

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发                                    | 一线修复                                 | 仍失败兜底                                          |
| --------------------------------------- | ---------------------------------------- | --------------------------------------------------- |
| 判新旧不准 (新建 vs 并入现有 active)    | `AskUserQuestion` 用户裁定               | 用户也不确定 → 默认新建, 保守留旧 task 不动          |
| 相关工作误判成独立 (拆多 task)          | 按相关性收敛: 相关 → 归一 task 拆 subtask (`subtask add`) | 已误建多 task → `skein archive` 多余者, 归一到主 task 补 subtask |
| 某阶段未达出口 (plan 未收敛 / check 未绿) | 停在该阶段, 禁跨阶段推进                  | 反复不过 → 走对应子 skill 兜底 (check 第 3 轮根因复盘) |
| 宣称派 agent 但无 `Agent` tool_use      | 立即在同回合补真实 `Agent` 调用          | 补不出 → 硬错停手, 禁回传「已派出 / 在做」           |
| 有 subtask 却想 inline 顺跑             | 停手, 走 skein-exec `claim→派 Agent` 循环, 每 ready subtask 派 1 subagent | 派不出 → 硬错停手, 禁 main 代跑 subtask              |
| 第二个 flow 进来, 第一个还没 durable    | 先给第一个 `skein create` 落盘再处理第二个 | 都未落盘 → 立即各自 `create`, 未处理者留 pending 待续 |

## ❌ 反例 (命中=流程错误)

> 🔒 Iron Law: 「派 agent」=真实 `Agent` tool_use — 无 tool_use 即没派, 禁回传「已派出」。

违反上文铁律即流程错误: main 直接改源码 / inline 跳 task / 宣称派 agent 无 tool_use / 无 worktree 改源码 / 直编 `.skein/task.md` / 纯文本代替 AskUserQuestion / exec 阶段问用户顺序 / **有 subtask 却 main inline 顺跑不派 subagent** / **第二个 flow 请求顶掉/中断在飞的第一个 task** / **相关工作拆成多个 task 而非归一 task 拆 subtask**。

### 自欺兜底 (高频反例)

| Excuse (自欺)                         | Reality (现实)                              |
| ------------------------------------- | ------------------------------------------- |
| 「agent 已经在跑了 / 我说已派出」     | 无 `Agent` tool_use = 没派, 硬错停手禁回传  |
| 「两个请求差不多, 先做新的」          | 顶掉在飞 task = 丢上下文, 先给旧的 durable 落盘 |
