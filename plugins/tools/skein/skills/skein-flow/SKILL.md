---
name: skein-flow
description: SKEIN task 闭环编排器 (plan→exec→check→finish)。$1 路由阶段, 缺省=flow 全闭环到 finish; 全空 (无参无描述)=清空模式, 把全部未完成 task 逐个跑到 finish。跨文件/多步或要求走 SKEIN 流程时用: 强制建 task, main 派 subagent 在 worktree 执行, 禁 inline 直改。
user-invocable: true
argument-hint: "[flow|plan|exec|check|finish] [任务描述/ID] (全空=清空全部未完成 task)"
arguments: ["flow|plan|exec|check|finish", "任务描述/ID"]
model: sonnet
effort: medium
---

# skein-flow — task 闭环编排器 (四阶段单一真值源)

**plan→exec→check→finish 四步闭环全流程编排。** 按首参路由阶段, **缺省 = flow 全闭环** (非 plan)。

## 🧭 参数路由

解析 `$1` (首个参数), 定阶段:

| `$1` | 阶段 | 行为 |
|---|---|---|
| **全空 (无 `$1` 无描述)** | **flow · 清空模式** | 不新建 task, 取 `skein list --status open --json`, 按 DAG 就绪序把**全部未完成 task** 逐个走完闭环到 finish (并发受 max_active 限)。列表为空 → 报「无未完成 task」即停 |
| `flow` / **缺省 / 任务描述** | **flow (默认)** | 走完整闭环 plan→exec→check→finish, 阶段间自动续跑不停顿。循环编排详见 [references/flow-loop.md](references/flow-loop.md) |
| `plan` | **plan** | **仅规划** — 判新旧 + create/并入 + brainstorm + grill 硬门, 推到就绪即停 (停在 `skein start` 前) |
| `exec` | **exec** | 驱动就绪/在途 task 走完整闭环到 finish (start→exec→check→finish) |
| `check` | **check** | exec 产物完成后、finish 前, 派 `Agent(subagent_type="skein:skein-checker")` 跑验证 |
| `finish` | **check 全绿后** | 派 `Agent(subagent_type="skein:skein-finisher")` 勘察 + skein finish 闭环 + 异步 sediment |

🔒 **禁把缺省当 plan 用** — 无参 / 只给任务描述 = 用户要**做完**, 不是要个规划稿。plan 收敛后禁停手问「要不要开始执行」, 直接续 exec。只有显式 `/skein-flow plan` 才停在就绪。

🔒 **全空 = 清空存量, 禁走 plan** — 无 `$1` 且无任务描述时无新需求可规划, 直接进 exec 消化存量: `待处理` 态先补 plan 收敛再 start, `就绪 && ready=true` 直接 start, `进行中/检查中` 续跑当前阶段。禁凭空造 task、禁问用户「要做什么」。

**载体铁律 + 正向配方** — 「派 agent」=真实 `Agent` tool_use, `subagent_type` 用带前缀全名 `skein:skein-executor` / `skein:skein-checker` / `skein:skein-finisher` (**照抄形式见 [carrier-rules.md 派发调用形式](references/carrier-rules.md#派发调用形式-照抄-禁自由发挥)**) / **禁 teammate·agent-team (禁传 `team_name`, 禁 `SendMessage`)** / main 默认禁写源码 / 有 task 必有 worktree / dispatch 6 字段 / 完成即时回传 / 并发请求禁互相顶掉 等 12 条铁律, 及命中即流程错误的正向配方表, 全量详见 [references/carrier-rules.md](references/carrier-rules.md)。

## 🛑 状态先行三硬门 (单一真值源)

| 硬门 | 门规 | 违反后果 |
|---|---|---|
| 1. task 级 | 未 `skein confirm` (**须先拿到用户批准**) 禁进 exec。**就绪即可调度** — `claim exec` 会在首个 subtask 被认领时自动 `start` (建 worktree + 进行中), 不必手工先 start | 流程错误, 回退补 confirm |
| 2. subtask 级 | 未 `skein claim exec`/`subtask start` 占槽禁派 agent | 已派视为无槽, 需回收补占槽 |
| 3. check 级 | 未 `skein check` (进行中→检查中) 禁跑验证/宣告结果 | 验证无效, 需重走 check |

🔒 **禁自降级** — 无"简单的可直接"口子, 任一借口 (「这个简单」「先做起来再说」「差不多勾满了」等) 均不构成豁免。详见 [references/state-before-action.md](references/state-before-action.md)、[task-state-machine.md](references/task-state-machine.md)、[subtask-state-machine.md](references/subtask-state-machine.md)。

---

# plan 阶段 (planning 入口 + 真值源)

判新旧 + 登记 + brainstorm + grill, 产出 planning 工件。**全程 main 同步前台** — brainstorm/grill 需逐问用户 (`AskUserQuestion`), subagent 不能与用户对话, 故不派执行 subagent (纯信息调研可派 `skein-researcher` 只读 subagent)。

## 触发

`$1=plan` (仅规划, 停在就绪) 或 `$1` 缺省/flow (走完整闭环, plan 收敛后自动续 exec)。

## 🛑 grill 硬门 (未过禁进 exec · STOP)

判新旧 + 登记 + brainstorm 收敛后, 委托 `skein-grill` 全轴对抗校对, 重点确认「用户想法 = PRD 写的」。弱点表交用户过, 补齐后放行。**未跑 grill 禁进 exec**; grill 未完成或弱点表未补齐 → 停在本步, 禁推进。

## ✅ plan 阶段完成判据 (勾满才转 exec)

- [ ] 用户诉求已逐条映射到 task (一句话可能对应 1 个 / N 个 / 部分并入已有 task), 各 task 已 `create` (含可读 slug)
- [ ] prd.md 已填完 (四章 `- [ ] TODO: 填X` 占位**已全部整行替换**为真实内容; **目标/验收标准两章条目一律保持 `- [ ]` 未勾 — 勾选归 check 阶段**)
- [ ] subtask 已规划 (`subtask add` 落 task.json DAG)
- [ ] 设计方案已定 (design.md 正文; 或 main 判定豁免)
- [ ] 预计工时已填 (`skein estimate <id> --set <小时数>`; `skein confirm` 硬校验非空正数)

未勾满 = planning 未收敛, 禁 `skein start` / 禁转 exec。`skein confirm` 亦会逐项硬拒 (subtask/prd/预计工时任一缺失即报错阻断)。

### 🛑 人审门: PRD 必须用户确认才进就绪 (每个 task 各审一次)

结构门 (prd / subtask / 工时) 过完还有一道**人审门** —— 那三道校验的都是结构, main 自己就能
填满再自己 confirm, 没有这道门「用户确认」名存实亡。**裸 `skein confirm <id>` 会被拒。**

两条合法来源, 都要真实用户动作:

| 来源 | 怎么走 | 强制力 |
|---|---|---|
| **看板点击** | 用户在 task 详情面板 / 详情页点「确认规划」 | 最强 — main 没有浏览器, 物理上点不了 |
| **对话确认** | main 走下面三步 | 靠流程纪律 (与「有没有真的派 agent」同级) |

```
1. skein confirm <id> --summary        # 取 PRD 审核摘要 (只打印, 不改状态)
2. AskUserQuestion                     # 把摘要给用户, 问「批准进就绪 / 要改」
3. skein confirm <id> --approved       # ← 仅在用户选了批准之后
```

- 用户选「要改」→ 回 planning 改 prd/subtask/工时, 改完重走, **禁跳过**。
- 多个 task **逐个各问一轮**, 禁一次 `AskUserQuestion` 打包批准多个 (用户没法逐份看)。
- `AskUserQuestion` 要给真选择 (批准 / 要改哪里), 禁只给「确认」一个选项当走过场。
- 看板已开着时, 也可以直接把 task 详情页链接给用户让其点 —— 比走对话更省事且更硬。

🛑 **没真问过用户就传 `--approved` = 伪造用户审核**, 与「宣称派了 agent 但无 tool_use」同级的
流程错误。

**完整 plan 阶段作业手册** (research 判定门 / 策略分档 / 复杂度天花板 / 判新旧登记 / brainstorm / 愿景翻译 / grill 契约锁定 / prd+design+subtask 产出 / dedup / 出口分流 / 失败模式) 详见 [references/for-plan.md](references/for-plan.md)。

---

# exec 阶段 (执行编排调度门)

只管执行编排 (职责划分 / 并行 / 依赖), 不碰需求 / 方案设计 (那归 plan)。main 作调度器编排, 改动落各 subtask 工作目录, 每个 agent 完成即回传。

## 触发

`$1=exec` (驱动就绪/在途 task 走完整闭环到 finish) 或 `$1` 缺省/flow (plan 收敛后自动续) 或**全空清空模式** (直接进本阶段消化 `list --status open` 全部存量)。

## 🛑 硬门

见状态先行硬门 1 (未 `skein confirm` 过人审门禁进 exec) + 硬门 2 (未 `claim` 占槽禁派 agent)。就绪态 task 直接 `claim exec` 即可, 首个 subtask 被认领时脚本自动启动该 task。**exec 无验收** — subagent 回传即执行完成, main 只 `done`/`fail`, 验收全归 check。

## ✅ exec 阶段完成判据

- [ ] 每 ready subtask 均已派真实 `Agent(subagent_type="skein:skein-executor")` 或已 done/fail (无遗漏挂起)
- [ ] `claim exec` 返回空且无 depends_on 死锁 (确认无可调度项)
- [ ] 全部 subtask done → 已自动进 check (不止于 subtask 全 done 就停手)
- [ ] 回合末已输出任务清单 (有异步在跑时)

**完整 exec 阶段作业手册** (入口路由 / 调度门载体分工 / 调度循环 (`max_active` 并发上限) / 自愈闭环 / tight feedback loop / 两条硬规 / 失败模式) 详见 [references/for-exec.md](references/for-exec.md)。

---

# check 阶段 (质量验证门)

exec 完成后、finish 前的**质量门**。**验证与修复分离**: `skein-checker` 只验证 (无写权), 失败交合适 agent 修。未过禁 finish。**禁动 design.md** (仅 planning 阶段 + check 失败回 planning 二次进入可写)。

## 触发

`$1=check` (exec 产物完成后、finish 前, 派 skein-checker 跑验证), 或 flow 全闭环内 exec 全 subtask done 自动进入。

## 🛑 硬门

见状态先行硬门 3 (`skein check` 状态切换归 `skein-checker` 自跑, main 只确认派发前 task 处于「进行中」态, 禁 main 在「进行中」态自跑验证当 check 结果)。

## ✅ check 阶段完成判据 (放行 finish 前勾满)

- [ ] checkpoint 核对: task 验收标准 + 各 subtask `--check` 项全完成
- [ ] 场景内置 check 全绿
- [ ] 契约逐条 pass (`skein contract` 全覆盖)
- [ ] 一致性核查零冲突
- [ ] 本轮通过的验收项已回写 `- [x]`

**完整 check 阶段作业手册** (验证流程 / checkpoint 核对 / 场景自适应内置 check / 判定 / 回 planning 重确认分档 / 重验放行) 详见 [references/for-check.md](references/for-check.md)。

---

# finish 阶段 (收尾闭环门)

check 全绿后的**收尾门**, 只做收尾 (勘察改动+悬挂 → 合并 → 销 worktree → 标记完成 → 异步 sediment), 不重做验收。**未 finish 闭环(标记完成) = 未闭环, 禁宣告 Done。**

## 触发

`$1=finish` (check 全绿后), 或 flow 全闭环内 check 放行后自动进入。前置硬门 = check 阶段完成判据全绿。

## 载体分工

派 finish 前 main 先确认本 task 派出的后台 agent 均已结束 (悬挂未清 = 未闭环, 禁派 finisher) → 派 `skein-finisher` 自主完成勘察改动 + 仓库根跑 `skein finish` (commit→merge→销 worktree→标记完成) → main 只读结果按 verdict 分流 (需处理时兜底) → 异步派 `skein-specer` 做 sediment (finish 先闭环, main 不等回传)。

## ✅ finish 阶段完成判据 (勾满才算闭环)

- [ ] finisher 回传 verdict=收尾干净 (或「需处理」已按失败模式表处理完并重派确认干净)
- [ ] `skein finish` 已成功 (finisher 自跑, commit→merge→销 worktree→标记完成)
- [ ] sediment 已异步派出 (不等回传)
- [ ] `.pending-fix` 标记已检测 (有则 auto-fix bg 已派, 无则跳过)

**完整 finish 阶段作业手册** (流程步骤 / 失败模式表含 merge 冲突处理 / auto-fix 双保险) 详见 [references/for-finish.md](references/for-finish.md)。

---

# 通用部分 (全阶段适用)

## 作用域边界 (何时建 task)

**原则: 该走 flow 的直接走, 不问用户要不要走。能走 flow 还是 inline 是 AI 自己该判的选择, 禁抛给用户。** 🔒 禁自降级借口一律不构成豁免, 详见 [references/state-before-action.md](references/state-before-action.md)。

| 特征 | 判定 |
|---|---|
| 纯查询 / 文档阅读 / 问答 (无改动) | 豁免 (直接做) |
| 单文件单处改, ≤20 行且位置已知 | 豁免 (直接做) |
| 跨 ≥2 文件 / 单文件多处 / 多步骤 | **必建 task (直接走 flow)** |
| 需外部调研 / 产出文档交付 | **必建 task (直接走 flow)** |
| 边界模糊 (走 flow vs inline 难判) | AskUserQuestion 问用户 (禁自行 inline 蒙混) |

归一 vs 分立 / worktree 豁免 (**跨 ≥2 文件一律必建 task, 无「≤3 文件微改」等例外**) / 完成判定 详见 [references/scope-boundary.md](references/scope-boundary.md)。

**零外部 skill 硬依赖** — skein 四步闭环自包含覆盖全部场景, 场景路由已完全由上方策略分档 / research 判定门 / 复杂度天花板 / dedup / supertask 覆盖。

## 失败模式总表 (四阶段 + 通用合并去重)

| 阶段 | 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|---|
| 通用 | 判新旧不准 (新建 vs 并入现有 active) | `AskUserQuestion` 用户裁定 | 用户也不确定 → 默认新建, 保守留旧 task 不动 |
| 通用 | 相关工作误判成独立 (拆多 task) | 按相关性收敛: 相关 → 归一 task 拆 subtask | 已误建多 task → `skein archive` 归档多余者 |
| 通用 | 某阶段未达出口 (plan 未收敛 / check 未绿) | 停在该阶段, 禁跨阶段推进 | 反复不过 → 走对应阶段兜底表 |
| 通用 | 宣称派 agent 但无 `Agent` tool_use | 立即同回合补真实调用 | 补不出 → 硬错停手, 禁回传「已派出」 |
| plan | grill 弱点表 >3 轮不收敛 | 归并同源弱点批量 `AskUserQuestion` 裁定 | 仍发散 → scope 过大, 拆多 task (heavy 档) |
| plan | subtask 粒度不清 / depends_on 定不了 | 回 brainstorm 补边界重切 | 仍切不动 → 派 `skein-researcher` 勘察代码再拆 |
| exec | subtask 报错 (非阻塞) | 自愈: 定点重派 ≤2 轮 / 根因独立插修复 subtask | 修复也失败/超 scope → 停调度回传 (root-cause-protocol) |
| exec | subagent 返回 `需要:` | main 转达用户/补信息后重派 | 信息仍缺 → 挂起下游未 ready, 禁标 done |
| exec | `claim exec` 返回空 (满槽/无就绪) | 找 `待处理` 无 subtask 的 task 提前 plan 填空闲 | 全 pending 仍空 → 查 depends_on 死锁, 停手回 plan 改 DAG |
| check | 孤立失败 (单点 lint/type/test/契约) | 回 planning 重确认定修复方向, 加 1 定点修复 subtask | 反复不过 → 见下 check 第 3 轮路径 |
| check | 一致性冲突 / 根因跨 subtask | 加多个修复 subtask (一冲突一), 逐条覆盖 | 冲突未全覆盖禁 finish |
| check | 修复子任务 ≥2 轮仍 FAIL (第 3 轮) | 按 root-cause-protocol 5 维根因复盘 | 带根因回 planning 定向重修; 超 exec (需求/设计缺陷) → 转人工 |
| finish | finisher 报悬挂残留 | main 清理后再合并 | 清不掉 → 停手, 报用户裁 |
| finish | `skein finish` merge 冲突 | 读冲突文件手动解后重跑 finish | 解不开 → 停手保留 worktree, 报用户裁 |

各阶段完整失败模式明细详见对应作业手册: [for-plan.md](references/for-plan.md) / [for-exec.md](references/for-exec.md) / [for-check.md](references/for-check.md) / [for-finish.md](references/for-finish.md)。

## ✅ 正向配方 + 载体铁律 (命中反面=流程错误)

已并入 [references/carrier-rules.md](references/carrier-rules.md) — 11 条载体铁律 + 正向配方表合一, 单一真值源。
