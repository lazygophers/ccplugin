---
name: skein-flow
description: SKEIN task 闭环编排器 (plan→exec→check→finish, 另有 redo 断点续跑)。$1 路由阶段, 缺省=flow 全闭环到 finish; 全空 (无参无描述)=清空模式, 把全部未完成 task 逐个跑到 finish; redo <tid> = session 意外结束后复位孤儿 subtask 接着跑。跨文件/多步或要求走 SKEIN 流程时用: 强制建 task, main 派 subagent 在 worktree 执行, 禁 inline 直改。
user-invocable: true
argument-hint: "[flow|plan|exec|check|finish|redo] [任务描述/ID] [--plan] (全空=清空全部未完成 task)"
arguments: ["flow|plan|exec|check|finish|redo", "任务描述/ID"]
model: sonnet
effort: medium
---

# skein-flow — task 闭环编排器 (四阶段单一真值源)

**plan→exec→check→finish 四步闭环全流程编排。** 按首参路由阶段, **缺省 = flow 全闭环** (非 plan)。

## 🧭 参数路由

解析 `$1` (首个参数), 定阶段:

| `$1` | 阶段 | 行为 |
|---|---|---|
| **全空 (无 `$1` 无描述)** | **flow · 清空模式** | 不新建 task, 取 `skein list --status open --json`, 按 DAG 就绪序把**全部未完成 task** 逐个走完闭环到 finish (并发受 `pools.work` 限)。列表为空 → 报「无未完成 task」即停 |
| `flow` / **缺省 / 任务描述** | **flow (默认)** | 走完整闭环 plan→exec→check→finish, 阶段间自动续跑不停顿。循环编排详见 [references/flow-loop.md](references/flow-loop.md) |
| `plan` | **plan** | **仅规划** — 判新旧 + create/并入 + brainstorm + grill 硬门, 推到规划完成 (待处理) 即停 (停在 `skein confirm` 前) |
| `exec` | **exec** | 驱动待处理/在途 task 走完整闭环到 finish (confirm→exec→check→finishing→finish) |
| `check` | **check** | exec 产物完成后、finish 前, 派 `Agent(subagent_type="skein:skein-checker")` 跑验证 |
| `finish` | **check 全绿后** | 派 `Agent(subagent_type="skein:skein-finisher")` 勘察 + skein finish 闭环 + 异步 sediment |
| `redo <tid> [--plan]` | **redo (断点续跑)** | session 意外结束后, 复位该 task 全部「运行中」subtask (一律当孤儿) 并按当前所处阶段续跑剩余闭环。**必须带 tid**, 不接受全空清空模式; `--plan` 只到规划收敛即停, 不进 exec |

🔒 **禁把缺省当 plan 用** — 无参 / 只给任务描述 = 用户要**做完**, 不是要个规划稿。plan 收敛后禁停手问「要不要开始执行」, 直接续 exec。只有显式 `/skein-flow plan` 才停在规划完成态 (待处理, confirm 前)。

🔒 **全空 = 清空存量, 禁走 plan** — 无 `$1` 且无任务描述时无新需求可规划, 直接进 exec 消化存量: `待处理 && ready` → confirm; `待处理 && !ready` → 前置未清暂缓; **`待处理 && 缺 plan 产物 (prd 未填 / 无 subtask)` → 补 plan 收敛 (填 prd + 加 subtask + estimate) → confirm**; `调研中` 续跑调研收敛后再 `confirm`; `进行中/检查中/收尾中` 续跑当前阶段。禁凭空造 task、禁问用户「要做什么」。

**载体铁律 + 正向配方** — 「派 agent」=真实 `Agent` tool_use, `subagent_type` 用带前缀全名 `skein:skein-executor` / `skein:skein-checker` / `skein:skein-finisher` (**照抄形式见 [carrier-rules.md 派发调用形式](references/carrier-rules.md#派发调用形式-照抄-禁自由发挥)**) / **禁 teammate·agent-team (禁传 `team_name`, 禁 `SendMessage`)** / main 默认禁写源码 / 有 task 必有 worktree / dispatch 6 字段 / 完成即时回传 / 并发请求禁互相顶掉 等 12 条铁律, 及命中即流程错误的正向配方表, 全量详见 [references/carrier-rules.md](references/carrier-rules.md)。

## 🛑 状态先行三硬门 (单一真值源)

| 硬门 | 门规 | 违反后果 |
|---|---|---|
| 1. task 级 | 未 `skein confirm` (**须先拿到用户批准**) 禁进 exec。`confirm --approved` 已吸收原 `start` 全部职责 —— 通过即直接建 worktree 进**进行中**, 不必也不再有额外 `start` 步骤 | 流程错误, 回退补 confirm |
| 2. subtask 级 | 未 `skein claim exec`/`subtask start` 占槽禁派 agent | 已派视为无槽, 需回收补占槽 |
| 3. check 级 | 未 `skein check` (进行中→检查中) 禁跑验证/宣告结果 | 验证无效, 需重走 check |

🔒 **禁自降级** — 无"简单的可直接"口子, 任一借口 (「这个简单」「先做起来再说」「差不多勾满了」等) 均不构成豁免。详见 [references/state-before-action.md](references/state-before-action.md)、[task-state-machine.md](references/task-state-machine.md)、[subtask-state-machine.md](references/subtask-state-machine.md)。

---

# plan 阶段 (planning 入口 + 真值源)

判新旧 + 登记 + brainstorm + grill, 产出 planning 工件。**全程 main 同步前台** — brainstorm/grill 需逐问用户 (`AskUserQuestion`), subagent 不能与用户对话, 故不派执行 subagent (纯信息调研可派 `skein-researcher` 只读 subagent)。

## 触发

`$1=plan` (仅规划, 停在规划完成态 (待处理, confirm 前)) 或 `$1` 缺省/flow (走完整闭环, plan 收敛后自动续 exec)。

## 🛑 grill 硬门 (未过禁进 exec · STOP)

判新旧 + 登记 + brainstorm 收敛后, 委托 `skein-grill` 全轴对抗校对, 重点确认「用户想法 = PRD 写的」。弱点表交用户过, 补齐后放行。**未跑 grill 禁进 exec**; grill 未完成或弱点表未补齐 → 停在本步, 禁推进。

## ✅ plan 阶段完成判据 (勾满才转 exec)

- [ ] 用户诉求已逐条映射到 task (一句话可能对应 1 个 / N 个 / 部分并入已有 task), 各 task 已 `create` (含可读 slug)
- [ ] prd.md 已填完 (四章 `- [ ] TODO: 填X` 占位**已全部整行替换**为真实内容; **目标/验收标准两章条目一律保持 `- [ ]` 未勾 — 勾选归 check 阶段**)
- [ ] subtask 已规划 (`subtask add` 落 task.json DAG)
- [ ] 设计方案已定 (design.md 正文; 或 main 判定豁免)
- [ ] 预计工时已填 (`skein estimate <id> --set <小时数>`; `skein confirm` 硬校验非空正数)

未勾满 = planning 未收敛, 禁 `skein confirm` / 禁转 exec。`skein confirm` 亦会逐项硬拒 (subtask/prd/预计工时任一缺失即报错阻断)。

### 🛑 人审门: PRD 必须用户确认才能 confirm 开工 (每个 task 各审一次)

结构门 (prd / subtask / 工时) 过完还有一道**人审门** —— 那三道校验的都是结构, main 自己就能
填满再自己 confirm, 没有这道门「用户确认」名存实亡。**裸 `skein confirm <id>` 会被拒。**

两条合法来源, 都要真实用户动作:

| 来源 | 怎么走 | 强制力 |
|---|---|---|
| **看板点击** | 用户在 task 详情面板 / 详情页点「确认规划」 | 最强 — main 没有浏览器, 物理上点不了 |
| **对话确认** | main 走下面三步 | 靠流程纪律 (与「有没有真的派 agent」同级) |

```
1. skein confirm <id> --summary        # 取 PRD 审核摘要 (只打印, 不改状态)
2. AskUserQuestion                     # 把摘要给用户, 问「批准开工 / 要改」
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

`$1=exec` (驱动待处理/在途 task 走完整闭环到 finish) 或 `$1` 缺省/flow (plan 收敛后自动续) 或**全空清空模式** (直接进本阶段消化 `list --status open` 全部存量)。

## 🛑 硬门

见状态先行硬门 1 (未 `skein confirm` 过人审门禁进 exec) + 硬门 2 (未 `claim` 占槽禁派 agent)。`confirm` 已吸收原 `start` 全部职责, 待处理 task 经 `confirm --approved` 后直接进**进行中**且已建好 worktree, 无需额外启动步骤, 随即 `claim exec` 派 agent 即可。**exec 无验收** — subagent 回传即执行完成, main 只 `done`/`fail`, 验收全归 check。

## ✅ exec 阶段完成判据

- [ ] 每 ready subtask 均已派真实 `Agent(subagent_type="skein:skein-executor")` 或已 done/fail (无遗漏挂起)
- [ ] `claim exec` 返回空且无 depends_on 死锁 (确认无可调度项)
- [ ] 全部 subtask done → `skein claim check` 认领进检查 (不止于 subtask 全 done 就停手)
- [ ] 回合末已输出任务清单 (有异步在跑时)

**完整 exec 阶段作业手册** (入口路由 / 调度门载体分工 / 调度循环 (`pools.work` 并发上限) / 自愈闭环 / tight feedback loop / 两条硬规 / 失败模式) 详见 [references/for-exec.md](references/for-exec.md)。

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

# redo 阶段 (断点续跑门)

session 意外结束 (窗口关/上下文爆/进程被杀) 后, 被派出去的 subagent 一起消失, 但占的槽还记在盘上:
subtask 停在「运行中」, 调度器认为满槽, task 卡死。`redo` 一键认领残局、复位死槽、接着往下跑到闭环。
**落在编排层, 不新增引擎命令** —— 复位动作全部用现有 `skein subtask` 命令拼, 拼法固定禁自由发挥。

## 触发

`$1=redo <tid> [--plan]` (与 plan/exec/check/finish 并列的第五个首参路由)。**必须带 tid**, 不接受全空
清空模式。**不传 tid**: 不裸报错 —— 扫描全部 task, 列出「进行中态且存在运行中 subtask」的候选清单
(卡死嫌疑名单) 供使用者从中选一个补 tid; 若候选为空, 明确回「无卡死 task, 无需 redo」。

**`--plan` 子参数**: 复位孤儿的动作照做 (解卡是刚需, 不受 --plan 影响), 但**只把规划推到收敛就停,
不自动进 exec** —— 分界点是「进 exec 前」。此子参数只对**起点归类为规划中** (待处理/调研中) 的 task 有
效: 续规划到收敛即停, 不再自动 `claim exec`/`confirm`。对**执行中/检查中/收尾中/已完成**起点, 规划早已在
更早阶段收敛过, `--plan` 没有可拦截的点, 行为与不带 `--plan` 一致 (仍复位/仍续跑) —— 但必须向使用者
说明「该 task 已过规划阶段, --plan 未生效」, 不能默不作声地照常执行让人误以为被拦下了。

## 🛑 孤儿判定口径 (动手前必须向使用者声明)

**全部「运行中」subtask 一律当孤儿, 不做存活探测/心跳/时长阈值** (2026-08-01 用户裁定) —— 误判一个
还活着的代价 = 重跑一个 subtask (可接受), 放过一个死槽代价 = task 永久卡死 (不可接受), 两者不对称。

🔒 **代价 (必须讲明, 不能藏)**: **redo 期间禁止有 agent 在跑** —— 若在有活 agent 时 redo, 会把活的
一起复位, 造成两个 agent 干同一件事、互相覆盖改动。编排层看不见 agent 存活, 无法用代码防, 只能动手前
把口径亮给使用者。

🔒 **redo 只改状态, 不回滚已产出的改动**: 复位动作只是把孤儿 subtask 的状态打回可调度 (运行中→失败→
运行中), 不删除、不撤销上一轮已经写出的任何文件改动 —— 那是上一轮的劳动成果, 且 subtask 重跑本来就
要求幂等。redo 解的是「槽被占死」这个卡点, 不是「回滚重来」。想丢弃某个 subtask 已产出的改动, redo
不提供这个能力, 需另想办法 (如手工 revert)。

## 起点分流: 按 task 当前所处阶段续什么

不预设卡在哪一步, 先 `skein status <tid>` 读当前态分流:

| task 当前 `status` | redo 做什么 |
|---|---|
| 待处理 | 无运行中 subtask 可复位 (未 confirm 无 worktree). 续规划到收敛, 走人审门 confirm |
| 调研中 | research subtask 与 exec 同占 `pools.work` 槽, 可能有孤儿 — 走复位步骤后续跑调研到全 done, `skein plan` 收敛回待处理 |
| 进行中 | 复位全部运行中孤儿 subtask (见下方复位步骤) → 重新调度 → 续跑剩余闭环 |
| 检查中 | check 不设 subtask, 无运行中 subtask 可复位, 直接重派 `Agent(subagent_type="skein:skein-checker")` |
| 收尾中 | finish 同样不设 subtask, 无运行中 subtask 可复位, 直接重派 `Agent(subagent_type="skein:skein-finisher")` |
| 已完成 | 报「已闭环, 无事可做」, 不做任何操作 |

`检查中`/`收尾中` 现为状态机里两个独立落盘态, `skein status <tid>` 直接读得到, 不再需要旧版靠验收
标准覆盖率二次判定"验证中 vs 收尾中"。

## 复位步骤 (进行中态专用, 命令固定禁改拼法)

1. `skein subtask list <tid>` → 筛 `status` 列为 `运行中` 的全部 sid。无结果 → 跳过 2/3, 直接
   `skein claim exec` 回正常调度循环。
2. 对每个孤儿 sid **逐个**执行 (引擎无 `运行中→待处理` 直接迁移, 只有
   `运行中→失败→运行中`, 这是唯一拼得出的等价路径):
   ```
   skein subtask fail <tid> <sid> --note "redo 孤儿复位: session 意外退出, 全部运行中一律当孤儿"
   skein subtask start <tid> <sid>
   ```
3. `skein claim exec` 补齐 pending 池待认领项, 之后按 [references/for-exec.md](references/for-exec.md)
   常规流程续跑到全 subtask done → check。

## 🔒 复位后必报: 被复位清单 (动手后必须回传使用者)

复位步骤跑完 (无论动了几个孤儿), 必须回传一份清单让使用者核对有没有误伤 —— 不做交互确认, 但这份清单
是硬性的, 不能省:

```
redo <tid> 已复位以下 subtask (运行中 → 失败 → 运行中, 重新可调度):
- r1: 原运行中, 判定孤儿, 已复位
- r2: 原运行中, 判定孤儿, 已复位
无需复位: r3 (已完成), r4 (待处理)
```

第 1 步无孤儿 (进行中态但当前无运行中 subtask) → 清单退化为一行:
`redo <tid>: 无运行中 subtask 需复位, 直接续调度。`

**完整 redo 阶段作业手册** (起点分流细节 / 复位步骤边界情况 / 与状态机的对应关系) 详见 [references/for-redo.md](references/for-redo.md)。

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
