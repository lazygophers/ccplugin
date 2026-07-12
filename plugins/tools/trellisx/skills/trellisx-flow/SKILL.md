---
name: trellisx-flow
description: '🔄 请求级入口: 把指定请求强制纳入 trellis task 闭环 (plan→exec→check→finish), 禁 inline (即使极简)。用户显式调用 (/trellisx-flow) 或 model 自动触发 (请求复杂/多步/跨文件时)。调用即创建同意信号, 仍先判新建 vs 并入 active task。与 trellisx-apply 互补 —— apply 注入"推荐建 task"常驻软提示指向本 skill, 由本 skill 接管。载体默认 subagent 编排 (main 调度 trellis-implement 共享 task worktree 并发 2)'

argument-hint: "[--worktree|--no-worktree] <任务描述>"
arguments: [载体选项 (可选), 任务描述]
---

# trellisx-flow — 强制 Trellis task 闭环

用户**显式调用**本 skill, 要求把其指定的请求**强制作为 Trellis task 处理**, 禁止 inline 直接做 (即使看起来简单)。调用本 skill 即「创建同意」信号 —— 跳过"要不要建 task"的询问 (用户已表态: 要)。但 **调用本 skill ≠ "新建 task"** —— 仍须先判这是**全新任务**还是**对现有 active task 的补充/延续**, 再决定新建还是并入。

处理对象 = 用户调用本 skill 时给出的请求 (任务描述 / arguments)。

## 入参 (调用时覆盖默认载体策略)

调用形如 `/trellisx-flow [选项...] <任务描述>`。**选项位于任务描述之前**, 缺省即走本 skill 默认 (= 现状, 见下表「缺省」列)。无法识别为选项的 token 一律并入任务描述, 不报错。

| 选项 | 作用 | 缺省 (无此选项) |
|---|---|---|
| `--worktree` | 强制 exec 走 worktree 隔离 (= 默认, 仅显式声明用) | **强制 worktree** |
| `--no-worktree` | 禁 worktree 隔离: exec **仍派 subagent** 执行 (main 仍禁亲改源码), 但**不开 worktree, 直接在主工作区改** | — |

- **互斥冲突** (`--worktree` 同时 `--no-worktree`) → 🛑 STOP, `AskUserQuestion` 让用户裁定, 禁自选。
- **优先级**: 入参 > 本 skill 默认。`--no-worktree` **只放宽 worktree 隔离这一条**, 不放宽"main 默认禁写源码 / 实质工作派 subagent" —— exec 永远是 subagent, 只是改主工作区而非 worktree。
- **`--no-worktree` 对 finish 的影响**: 无 worktree 分支可合并, 改动已在主工作区 → finish 跳过"合并多 worktree 分支 / 销 worktree", 直接 commit 主工作区改动 + archive。
- **中文别名** (同义可接): `强制worktree`=`--worktree`; `禁worktree`/`禁止worktree`=`--no-worktree`。

## 执行载体铁律 (最高优先级)

> **概念分清**: **task** = trellis 任务记录 (由 `task.py create/start/finish/archive` 脚本管理), 由 **main 同步跑**。**实质工作** (改源码 / 跑 check) **派 subagent 编排执行** (**main 是调度器** → 派各 `trellis-implement` 各执行 1 subtask, 共享 task worktree, 动态 DAG 调度并发上限 2 完成即派, 见 trellisx-orchestrate `scheduling.md`; trellis-implement 不调度不递归, Recursion Guard), 不在 main 上下文里直接做。是否 `run_in_background` 异步 / 是否并行 **按需自定, 本 skill 不强制**。**注意: worktree 隔离不在「按需」之列 —— 有 task 必有 worktree (task 级, 默认 1 task 1 worktree); fan-out subtask 共享 task worktree (subtask 与 worktree 无绑定, 不为 subtask 单独开); 多 worktree 允许 (opt-in, 非自动); 唯一例外是调用带 `--no-worktree` (见「入参」段), 此时仍派 subagent 但改主工作区。**

- 🔴🛑 **"派 agent" = 真实调用 `Agent` 工具, 不是叙述 (最易踩, 必守, 铁律首项)** —— 每个"派 agent"动作 MUST 在**同一回复**里产生真实的 `Agent` tool_use。**严禁在本回复无 `Agent` 工具调用的情况下, 回传"已派出 / agent 在做"等措辞 —— 宣称 ≠ 调用, 那是幻觉, 等于跳过执行**。同理 task/看板/worktree 的"已建/已登记"必须是真实跑过命令或工具的结果, 禁凭空宣称。
  > **回传前自检**: 任何"agent 已派 / 在跑 / 已建 task / 看板已更新"措辞输出前, 确认本回复**确有对应的 tool_use** (Agent / Bash task.py / trellisx-workspace)。无 → 先发起真实调用, 禁先回传。
- ⛔ **main 默认禁写源码 (实质工作优先派 subagent)** —— 改源码、跑 check 等**实质产出派 subagent 编排执行** (默认载体, 见上「概念分清」)。**仅特别情况例外** (≤3 文件微改 / subagent 难处理的上下文密集决策 / 用户显式要求), 且必在 task worktree 内写; 例外不改变"优先派 subagent"原则。
- 🧩 **exec/check 派 subagent 编排** —— **main 是调度器**, 动态 DAG 调度派各 `trellis-implement` 各执行 1 subtask (并发上限 2, 完成即派, 见 trellisx-orchestrate `scheduling.md`), fan-out 的 trellis-implement 共享 task worktree (subtask 不绑定 worktree); trellis-implement 不调度不递归 (Recursion Guard)。
- 🌳 **有 task 必有 worktree (task 级隔离, 强制, 与载体无关)** —— task 在其 worktree 内执行, 主工作区零改动; 默认 1 task 1 worktree。**唯一例外: 调用带 `--no-worktree` → exec 仍派 subagent 但改主工作区 (见「入参」段)**。完整规则 (1 task 1 worktree 默认 / subtask 共享 task worktree 不绑定 / 多 worktree 允许 opt-in 非自动, finish 映射合并 / 异步并行按需) 见「硬规」段 §其他必做。
- 💬 **planning 委托 `/trellisx-add --continue`, 不派 subagent** —— flow 不复制 planning 正文, 运行时委托 `trellisx-add` (判新旧+登记+brainstorm+grill 硬门1 全在 add)。add 的 brainstorm 需逐问用户 (交互式), subagent 不能 `AskUserQuestion` / 与用户对话, 故 planning 全程 **main 同步前台** (`--continue` 借完产物 flow 自接激活), 不派 subagent。
- 🗂️ **task 生命周期脚本由 main 同步跑** —— `task.py create / start / finish / archive` 是任务记录管理, **main 直接同步执行** (不派 agent、不算实质工作); `task.py finish` 后由 `after_finish` hook 自动完成 commit→merge→archive→销 worktree (多 worktree 时各分支经映射合并)。
- 🧹 **finish 清理 (强制)** —— `task.py finish` 前 MUST 关停本 task subagent + 无悬挂后台任务, 未关 = 未闭环禁宣告 Done。完整规则 (`TaskList` 查 / `TaskStop` 关 / hook 合并多 worktree 分支销 worktree) 见「硬规」段 §其他必做。
- 🧑 **用户交互决策点 main 亲做** —— `AskUserQuestion` (判新旧不准、产物评审、scope 澄清) subagent 不能与用户对话; subagent 缺信息只能在返回里标 `需要: <问题>`, 由 main 转达用户。
- 📦 **每个 dispatch prompt 必须 6 字段自包含**: 目标 / 已知 (含 `Active task: <task.py current 路径>`) / 工作目录与范围 / 输出格式 / 验收标准 / 失败处理。缺字段不派。
- 📣 **完成即时回传** —— 每个 subagent 完成或阻塞, main **立即输出摘要回传用户**, 禁批量延迟汇总。
- 🔒 **task.md 禁直接 Edit/Write** —— `.trellis/task.md` 看板**必经 `trellisx-taskmd.py` 脚本操作** (settings.json `permissions.deny` + `guard-taskmd.sh` PreToolUse hook 双保险硬阻)。直接编辑会被 deny 拦 + hook exit 2 block, 并报"用脚本"。违 = 流程错误 (绕过 hook/AI 列分工 + 格式漂移)。
- 🧮 **多 task 并行调度 (同 session 多 active task)** —— **main 可在同一 session 内同时跟踪多个 in_progress task** (≠ 跨 session, 跨 session 本就独立):
  - **active 集 + focus**: `active_tasks` 列表存所有 in_progress task, `current_task` (= focus) 是默认操作对象 (最近 start 的)。`task.py current` 显示 focus; `task.py current --all` 列所有 active (focus 标 `<- current` 绿, 其余 `<- active` 青)。
  - **task 级并发上限 2** (`MAX_ACTIVE_TASKS`): 同 session active 集 ≤ 2。`task.py start` 第三个 → 报错 "task 级并发上限 2, 先 finish 一个", 禁超。 (= subtask 级上限, 见 scheduling.md)
  - **task 间冲突判定 (复用 subtask 级算法, 见 scheduling.md §2)**: 两 task 的 write-files glob 相交 或 exec-scope 相交 → 串行 (不能并行派 subagent); 不相交 → 可并行 (各 task 各 worktree, 各派 trellis-implement, 合计并发仍受每层上限 2 约束)。
  - **显式前置 (depends_on / 看板「前置」列)**: task.json 顶层 `depends_on` (**便携写入口 = `trellisx-taskmd.py update <tid> --deps "a,b"`**, 随 apply 发货, 无需改原生 task.py; 本仓另有 `task.py create --depends-on` / `task.py set-deps` 语法糖, 非发货路径; 看板「前置」列渲染) 是**显式 DAG 边**, 与冲突自算边**并集**成最终调度 DAG —— 被依赖 task 未 done 前, 依赖它的 task 不 ready (即使文件不冲突也不能先派)。无 `depends_on` 的 task 仅受冲突边约束。
  - **start/finish 语义**: `start <task>` 加入 active 集 (非顶替, 超上限报错); `finish` 从 active 集移除 focus + 自动切 focus 到剩余首个 (非清空所有)。
  - **DAG**: 最终 task 级 DAG = 冲突自算边 ∪ 显式 `depends_on` 边; 就绪 (所有前置 done + 无冲突占用) 的 task 并行派 subagent, 未就绪的串行等待 —— 与 subtask 级 §4 / child 级 §8 同构, 仅调度对象是 task。

## 调用边界 (重要)

- ✅ **双模触发**: ① 用户显式 `/trellisx-flow <描述>` 或点名; ② model 自动触发 —— 请求复杂 / 多步 / 跨文件 / 该建 task 时自动加载本 skill 强制走闭环。
- 🔗 **与 apply no_task 提示的关系**: `trellisx-apply` 在无 active task 时注入的常驻软提示 = 轻量"建议建 task", 指向本 skill; 本 skill 接管后强制走 plan→exec→check→finish。两者嵌套 (hint → flow 接管), 不冲突。
- ⛔ **仍禁**: 把明显该 inline 的极简请求 (纯查询 / 单文件 ≤20 行) 强行建 task (作用域边界见「硬规」段)。

## 强制流程 (plan → exec → check → finish, 不可跳步)

> **第 0 步 — 解析入参**: 进入下列流程前, 先从调用参数剥离前置选项 (`--worktree`/`--no-worktree` 及中文别名, 见「入参」段), 确定本次 worktree 策略; 剩余 token 即任务描述。互斥冲突 → 🛑 STOP 问用户。

> **贯穿全程: 及时维护 `.trellis/task.md` 看板** —— 下列每一步 (create/start/阶段推进/finish) 完成后, **立即用 `trellisx-workspace` skill 更新 `.trellis/task.md`** 看板表中该任务行 (id/名称/描述/状态/worktree)。看板落后于实际 = 维护失效。

> 载体速查: **planning 委托 `/trellisx-add --continue`** (main 同步前台, add 内 brainstorm 交互 + grill 硬门1, 不派执行 subagent); **exec/check 派 subagent 编排** (**main 调度** → 派各 trellis-implement 各执行 1 subtask, 动态 DAG 并发上限 2 完成即派, 共享 task worktree; 异步/并行按需; 见 trellisx-orchestrate `scheduling.md`); **task.py 脚本 (create/start/finish/archive) main 同步跑**。main 做编排 + 脚本调用 + 交互式 planning + 用户交互决策 + 完成回传 + 看板维护。

1. **planning (委托 `/trellisx-add --continue`)** (main 同步前台) — flow **不复制 planning 正文**, 运行时委托 `trellisx-add` (planning 单一真值源): 调 `/trellisx-add --continue <任务描述>` 完成 **判新旧 + `task.py create` 登记 + 交互式 planning** (brainstorm 主导需求/方案 + grill 硬门1 边问边写, 产出 `prd.md`[+ `design.md`] + `implement.md`, 详见 `trellisx-add` skill)。
   - 🔴 **必带 `--continue` (= 不阻塞)**: add 跑完 planning **不停**, 返回产物路径; 无参 add 才停在 start 前 (那是用户直呼 add 的入口行为, flow 委托必带 `--continue`)。判新旧/登记/看板维护/grill 硬门1 全在 add 内, flow **不重复**。
   - add 返回 planning 产物 (`prd.md`/`implement.md` 等路径) 后 → flow 自接下一步激活。
2. **激活** (main 编排) — 🔴 **grill 硬门 2 (需求确认, start 前必做)**: planning 产物齐 → MUST 调 `/trellisx-grill` 跑全轴 (A-L, 按工件动态裁剪) 对抗校对, 重点轴 A/B/C/E/G 确认用户想法 = PRD 写的。grill 弱点表交用户过, 用户确认"这就是我要的" + 弱点补齐后才放行。**未跑 grill 禁 start** (硬门)。通过后 → 产物**由 main 用 AskUserQuestion 交用户评审** → `task.py start` → status=in_progress。→ **更新 task.md 行** (状态 in_progress / 阶段 exec / worktree 路径)。
3. **exec** (subagent 编排, **worktree 强制隔离**) — 🔴 **main 是调度器, 动态 DAG 调度派各 `trellis-implement` 各执行 1 subtask** (并发上限 2, 完成即派下一个, 不空等全部, 见 trellisx-orchestrate `scheduling.md`) —— **默认 1 task 1 worktree** (subtask 共享其中, 不为 subtask 单独开); **多 worktree 允许** (opt-in, 非自动, 不靠 subtask 触发); **trellis-implement 不调度不递归** (工具集无 Agent/Task, Recursion Guard)。全部源码改动落 `<git根>/.worktrees/`, 主工作区零改动; **一律 agent 写代码, main 默认禁写源码** (仅特别情况例外)。worktree 为硬性要求 (有 task 必有 worktree), **仅**异步 (`run_in_background`) / 并行分组按需自定。**入参覆盖**: `--no-worktree` → 仍派 subagent 但改主工作区 (不开 worktree, 详见「入参」段)。每个 agent 完成即回传。→ **更新 task.md 看板**。

   🔴 **异步等待 MUST 输出任务清单 (硬规)** —— 凡 main 派出异步任务后**结束本回合前** (后台 sub-agent 在跑 / 审批等待), MUST 输出当前任务全景表格 (**4 列**: `id` · `状态` · `摘要` · `进度%`), 内容复用 main 已维护的 DAG 调度态 (见 trellisx-orchestrate `scheduling.md`), 不新算。**不触发**: 同步前台阻塞等待 (main 自己在等, 无独立清单) / 无在跑任务。完整格式 + 状态枚举 (固定中文: 进行中/等待中/阻塞) + 范例见 trellisx-orchestrate `progress-communication.md` §异步等待清单格式。

   🔴 **exec 阶段 subtask 间禁问用户顺序 (硬规)** —— 顺序决策**归 planning** (mermaid 调度图 + depends-on + 静态冲突 DAG, 见 trellisx-orchestrate `scheduling.md`)。exec 阶段 main 只跑动态调度循环: ready 即派、任一返回即查新 ready 立即派下一个、并发上限 2。**禁在任何 subtask 之间停下来问用户"先做哪个 / 下一个做什么 / 要不要继续"** —— 问序 = planning 没做透。**唯一例外**: planning 阶段就没定顺序 (PRD 缺调度图 / depends-on 缺失) → 🛑 STOP **退回 planning 补**, 不在 exec 问。用户执行中插新指令走中途修正路由 (改 PRD 真值 → SendMessage 通知在跑 agent), 不等于"问顺序"。
4. **check** (派 subagent fan-out) — checker agent 走 `trellis-check` 质量验证 (spec 合规 / lint / type-check / tests); 未过 → **再派 agent 修复重检**, 不跳 finish。→ **更新 task.md 阶段 check**。
5. **finish** (main 同步) — check 通过 → 🔴 **spec sediment 判定门 (finish 前必做, 非软约束)**: main 按下述 checklist 逐项判本 task 有无 spec 增量, 任一正向 ✅ → 走 `/trellisx-spec` sediment (提案→审批→写盘+同步 index.md) 再 finish; 全否 → 跳过:
   - **正向 (任一 ✅ 触发)**: ① 新命令式契约 (MUST/禁, 后续同类任务会再踩) ② 踩坑留痕 (debugging ≥2 轮才定位, 根因可写为可验证契约, 非一次性 bug) ③ 反复犯错 (同类错误在 ≥2 task journal 出现, grep 可验) ④ 跨任务可复用决策 (选型/架构边界/API 约定) ⑤ 验收基准 (本 task 可执行断言通用到能复用为 spec 验收条)
   - **排除 (NOT 触发)**: 一次性 bug / 本 task 私有实现细节 / 已有 spec 覆盖
   - **诚实边界**: 判定归 model 非脚本 (语义判断脚本做不了); 全无增量则跳过, 禁硬凑沉淀
   - **判定 trace (强制输出, 未输出 = 流程错误, 见反例 15)**: main MUST 按下表逐项 ✅/❌ 显式输出 (全否也要输出全 ❌ trace, 禁默默判"跳过"):
     ```
     sediment 判定 trace
     ═══════════════════
     正向 (任一 ✅ 触发 sediment):
       ① 新命令式契约 (MUST/禁, 后续同类任务会再踩): ✅/❌ (具体: <描述>)
       ② 踩坑 ≥2 轮 (根因可写可验证契约, 非一次性 bug): ✅/❌ (具体: <根因>)
       ③ 反复 ≥2 task (grep 可验): ✅/❌ (具体: <task list>)
       ④ 跨任务可复用决策 (选型/架构边界/API 约定): ✅/❌ (具体: <决策>)
       ⑤ 验收基准 (可复用断言): ✅/❌ (具体: <断言>)
     排除 (任一 ✅ 不触发, 仅当对应正向也 ✅ 时才需判):
       - 一次性 bug: ✅/❌
       - 本 task 私有实现细节: ✅/❌
       - 已有 spec 覆盖: ✅/❌
     判定: <触发 → 走 trellisx-spec sediment 提案 | 全否 → 跳过>
     ```
   再 **finish 前先确认本 task 的 subagent 已终止 + 无悬挂后台任务** (用 `TaskList` 查残留, `TaskStop` 关闭; **禁 `sleep`/轮询等后台任务跑完 —— 完成会自动回 notification, 届时本回合再走 finish**); 再 main 直接跑 `python3 ./.trellis/scripts/task.py finish`; `after_finish` hook 自动完成 commit→merge→archive→销 worktree (多 worktree 时合并各分支, 非派 agent, 非可选)。**`--no-worktree` 时**: 无 worktree 分支可合并, 改动已在主工作区 → finish 跳过合并/销 worktree, 直接 commit 主工作区改动 + archive。→ **更新 task.md 行** (状态 completed)。

## 失败模式 (三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| planning agent 返回标 `需要:` (缺需求/设计输入) | main 用 `AskUserQuestion` 转达, 回填答案重派 agent | 澄清后 scope 仍收不敛 → 🛑 STOP, 让用户直接拍板 MVP 边界 |
| exec agent 失败/报错返回 | 读失败原因, 补 dispatch prompt 已知/缩范围, 重派 | 同一 subtask 连续 2 次失败 → 🛑 STOP 回传用户, 转人工或拆更小 subtask |
| check 反复不过 (≥2 轮) | 派 agent 按 `trellis-check` 报告定点修复重检 | 第 3 轮仍不过 → 🛑 STOP, 加载 `trellis-break-loop` 跳出调试循环 |
| finish 时 worktree 合并冲突 | `after_finish` hook 自动 abort + 报冲突文件清单 | 检 finish 输出有 `trellisx-finish` 冲突告警 → 停, 转手动解, **禁强解 / 禁当成功** |
| 判不准「新建 task」还是「并入现有」 | `AskUserQuestion` 问用户裁定 | 用户必答 (禁自行替用户决定) |
| 非 trellis 项目 (无 `.trellis/`) | 提示用户先 `trellis init` | 用户拒绝 → 退出, 不强行建 task |

## 硬规 (正向必做)

### 作用域边界 (何时建 task)

| 特征 | 判定 |
| --- | --- |
| 纯查询 / 文档阅读 / 问答 (无改动) | 豁免, 不建 task |
| 单文件单处改, ≤20 行且位置已知 | 豁免 |
| 跨 ≥2 文件 / 单文件多处 / 多步骤改 | **必建 task** |
| 需外部调研 (库选型/方案对比) 或产出文档交付 | **必建 task** (调研为 research subtask) |
| 边界模糊 | **MUST AskUserQuestion 由用户裁定** |

**无 task → 不进执行编排 → 执行规约豁免**。Planning 阶段不派执行 subagent: brainstorm 主线由 main 同步前台 (subagent 不能 AskUserQuestion); 纯信息调研可派 trellis-research 并行, 但设计决策由 main 汇总裁定。

### 其他必做

- ✅ **走完 plan→exec→check→finish 闭环** —— **未 archive = 未完成, 禁宣告 Done / 禁结束本轮**。
- 🌳 **exec 必走 worktree 隔离 (强制, 除非 `--no-worktree`)** —— 写代码 subagent 在**本 task 的 worktree 内**执行 (共享, subtask 与 worktree 无绑定), 改动落 `<git根>/.worktrees/`, 主工作区零改动; finish 后由 `after_finish` hook 销 worktree。worktree 非可选 (有 task 必有 worktree, 默认 1 task 1 worktree), 只有异步/并行/多 worktree 才按需自定。**唯一豁免: 调用带 `--no-worktree` → subagent 改主工作区 (见「入参」段); main 默认禁写源码这条 `--no-worktree` 不豁免。**
- 🧹 **finish 前清理悬挂任务 (强制)** —— `task.py finish` 前 MUST 确认本 task 的 subagent 已终止、无悬挂后台任务 (`TaskList` 查残留, `TaskStop` 关闭); 任务未关 / worktree 未销 = 未闭环, **禁宣告 Done**。
- 📋 **异步等待 MUST 输出任务清单 (强制)** —— 派出异步任务后结束本回合前 (后台 sub-agent / 审批等待), MUST 输出任务全景表格 (4 列: id/状态/摘要/进度%, 见 exec 阶段同条 + trellisx-orchestrate `progress-communication.md` §异步等待清单格式)。同步前台阻塞等待 / 无在跑任务不触发。
- ✅ **及时维护 task.md 看板** —— 每个生命周期节点 (create/start/阶段推进/finish) 后用 `trellisx-workspace` 更新 `.trellis/task.md`; 看板滞后视为流程缺陷。

## ⛔ 反例黑名单 (命中任一 = 流程错误, 改方案重来)

| # | 禁做 | 改为 |
|---|---|---|
| 1 | main 直接改源码 / 跑 check (非特别例外) | 派 subagent 编排执行 (默认载体; 仅 ≤3 文件微改等特别情况例外, 必在 task worktree 内) |
| 2 | 把 task.py 脚本派 agent 执行 | `task.py create/start/finish/archive` main 同步跑 |
| 3 | inline 跳过 task (即使请求极简) | 一律走 task 闭环 —— 这是本 skill 全部意义 |
| 4 | check 未过就推进 finish | 先定点修复重检 |
| 5 | check / finish 未走完就宣告 Done | 未 archive (worktree 仍在) = 未闭环 |
| 6 | 把明显该 inline 的极简请求 (纯查询 / 单文件 ≤20 行) 强行建 task | 该 inline 的 inline, 作用域边界表判 (见「硬规」段) |
| 7 | main / agent 自行凭空设计需求方案 | `trellis-brainstorm` 主导需求, `trellisx-orchestrate` 仅执行编排 |
| 8 | 用 `trellisx-orchestrate` 做需求 / 方案设计 | 它只管 subagent 职责划分 / 并行 / 依赖 |
| 9 | 纯文本提问代替 `AskUserQuestion` | 用户确认 / 选择必用工具 |
| 10 | 批量延迟汇总 agent 进度 | 每个 agent 完成 / 阻塞即时回传 |
| 11 | **口头宣称"已派 agent / 已建 task / 看板已登记"但本回复无对应 tool_use** | **先真实调用** `Agent` / `Bash task.py` / `trellisx-workspace`, 再回传 —— 宣称 ≠ 调用, 凭空宣称 = 幻觉跳步 |
| 12 | exec subagent 直接在主工作区改源码 (无 worktree) **且未带 `--no-worktree`** | 必在本 task 的 worktree 内执行 (共享, subtask 不绑定 worktree), 改动落 `<git根>/.worktrees/`, 主工作区零改动 (带 `--no-worktree` 则允许改主工作区, 但 main 仍默认禁写) |
| 13 | finish 时留悬挂 subagent / 后台任务未关 | 改为 `TaskList` 查 + `TaskStop` 关后再 finish |
| 14 | exec 阶段 subtask 之间停下来问用户"先做哪个 / 下一个做什么" | 顺序归 planning, exec 只跑调度循环 (scheduling.md §4) —— ready 即派 / 完成即派 / 并发 2; PRD 缺调度图 → 退回 planning 补, 不在 exec 问 |
| 15 | finish 步 sediment 判定未输出 trace (默默判"全否跳过", 用户无感知) | MUST 按 trace 模板 (步骤 5 finish) 逐项 ✅/❌ 显式输出, 全否也要输出全 ❌ trace, 禁跳过 |
| 16 | 直接 Edit/Write `.trellis/task.md` (绕过脚本) | 经 `trellisx-taskmd.py` (show/update/sync/cleanup/map-*) —— deny + hook 双保险硬阻, 违 = 流程错误 |
| 17 | 同 session active 集超 2 (start 第三个 task) | task 级并发上限 2, 先 finish 一个再 start (与 subtask 级上限一致, 见 scheduling.md) |

> 与 `trellisx-apply` 的分工: 本 skill = task 强推主路径 (用户显式 + model 自动, 复杂多步跨文件即接管); apply 注入的 no_task = 轻量"建议建 task"常驻软提示, 指向本 skill。两者嵌套 (hint → flow), 不冲突。
