---
name: skein-flow
description: SKEIN task 闭环编排器 (plan→exec→check→finish 单一真值源)。按参数路由各阶段 — flow (缺省, 全闭环一路推到 finish) / plan 规划真值源 (判新旧 + create 登记 + brainstorm + grill 硬门, 产 prd/design/subtask DAG) / exec 执行编排调度 (双层 DAG, 完成即派, 并发 2, main 禁亲改源码) / check 质量门 (lint/type/test/契约 + 一致性核查, 验证修复分离) / finish 收尾闭环门 (勘察 + merge + 销 worktree + 标记完成 + 异步 sediment)。复杂/多步/跨文件请求, 或用户显式要求把请求作为 SKEIN task 处理时使用 — 强推闭环, main 作调度器派 subagent 在 worktree 内执行, 禁 inline 直接做。默认无参 = flow 全闭环 (plan→exec→check→finish 一路推到 finish, 不停在 plan)。
user-invocable: true
argument-hint: "[flow|plan|exec|check|finish] [任务描述/ID]"
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
| `flow` / **缺省 / 任务描述** | **flow (默认)** | 走完整闭环 plan→exec→check→finish, 阶段间自动续跑不停顿。循环编排详见 [references/flow-loop.md](references/flow-loop.md) |
| `plan` | **plan** | **仅规划** — 判新旧 + create/并入 + brainstorm + grill 硬门, 推到就绪即停 (停在 `skein start` 前) |
| `exec` | **exec** | 驱动就绪/在途 task 走完整闭环到 finish (start→exec→check→finish) |
| `check` | **check** | exec 产物完成后、finish 前, 派 skein-checker 跑验证 |
| `finish` | **check 全绿后** | 派 skein-finisher 勘察 + skein finish 闭环 + 异步 sediment |

🔒 **禁把缺省当 plan 用** — 无参 / 只给任务描述 = 用户要**做完**, 不是要个规划稿。plan 收敛后禁停手问「要不要开始执行」, 直接续 exec。只有显式 `/skein-flow plan` 才停在就绪。

**载体铁律**: 「派 agent」=真实 `Agent` tool_use / main 默认禁写源码 / 有 task 必有 worktree / dispatch 6 字段 / 完成即时回传 / 并发请求禁互相顶掉 等。全量 11 条铁律详见 [references/carrier-rules.md](references/carrier-rules.md)。

**状态先行铁律 (state-before-action)** — 三环节硬门 (task 级未 start 禁 exec / subtask 级未 claim 占槽禁派 / check 级未 skein check 禁验证宣告), 任一违反 = 流程错误回退到对应状态命令。🔒 禁自降级 — 无"简单的可直接"口子 (memory: `skein-hook-no-self-downgrade`)。详见 [references/state-before-action.md](references/state-before-action.md)、[task-state-machine.md](references/task-state-machine.md)、[subtask-state-machine.md](references/subtask-state-machine.md)。

---

# plan 阶段 (planning 入口 + 真值源)

判新旧 + 登记 + brainstorm + grill, 产出 planning 工件。**全程 main 同步前台** — brainstorm/grill 需逐问用户 (`AskUserQuestion`), subagent 不能与用户对话, 故不派执行 subagent (纯信息调研按下方「research 判定门」决定是否派 `skein-researcher` 只读 subagent)。

## 🧭 research 判定门 (自动判, 非用户说要才派)

brainstorm 前先定**是否需要派 skein-researcher**, 按信号分档自动判:

| 档 | 信号 | 判定 |
|---|---|---|
| **明确需** | 外部 API / 库选型 / 跨陌生子系统 / 现状代码未知 / 协议待定 | **自动派 researcher** |
| **明确不需** | 已知代码模式 / 用户给足信息 / 单熟悉子系统 / 单点改 | **跳 research, 直 brainstorm** |
| **保守灰区** | 倾向需但不明确 (可能涉未知但不确定) | **自动派 researcher** (宁可调研) |
| **激进灰区** | 倾向不需但拿不准 (看似简单但可能有坑) | **AskUserQuestion 问用户是否需 research** |
| **兜底** | brainstorm 中 subtask 切不动 / depends_on 定不了 | **触发派 researcher** 勘察代码再拆 |

派 researcher 后仍受「探索封顶」约束 — 够拆 subtask 即收敛, 禁无限深挖。结论持久化在 `.skein/task/<id>/research/`, planning 后续步骤可复读。

**探索封顶, 尽早转异步** — 登记 task 后目标是尽快填好 prd + subtask DAG 就转 exec 异步并行执行。调研够用即停: 只查够拆出 subtask + 定依赖所需的信息, 达到能拆分即收敛, 禁为求完备无限深挖。

**🧠 smart zone / context hygiene (ask-matt 同源)** — grill→prd→subtask DAG 三步应在**同一不中断 context window** 内完成, 保持思考连贯。接近 smart zone (~120k token) 上限 → 先收敛: 派 `skein-researcher` 异步卸载调研 / 压进 prd.md/design.md 工件 → 腾出窗口继续, **禁 degraded 状态硬推**。

## 策略分档 (轻量路由启发)

判新旧后先给任务定档, 决定 planning 力度 (**仅路由启发, 非新增机器/字段**):

| 档 | 判据 | 走法 |
|---|---|---|
| `direct-fix` | 单点微改, 在作用域边界表豁免范围内 | 不建 task, 直接改 |
| `standard` | 跨文件 / 多步, 单 task 可覆盖 | 常规 plan→exec→check→finish |
| `heavy` | 跨子系统 / 破坏式重构 / 多 task 并行 | 强化 grill + 可能拆多 task + 显式 `depends_on`。破坏式重构 (改契约/删旧路径/全站点一次改齐, 禁垫片) 见 [references/breaking-refactor.md](references/breaking-refactor.md) |

### 🛑 复杂度天花板 (归一有上限, 命中必提醒用户拆多 task)

归一是默认, 但**单 task 有复杂度天花板** —— planning 拆完 subtask 后 (subtask 数已知) 逐项对表, **命中任一即停下**, 用 `AskUserQuestion` 提醒用户「本 task 过复杂, 建议拆成多个互相依赖的 task」:

| 天花板信号 | 判据 |
|---|---|
| subtask 数超阈值 | 拆出 subtask **> 8** (或 brainstorm 已看出会 > 8) |
| 跨子系统 / 多改动面 | scope 跨 ≥2 子系统 / 多个独立改动面 |
| 工期 / 风险高 | 预估工期长 / 破坏式重构 (heavy 档) / 一处崩全批停 |

- **用户选拆** → 按子系统 / 改动面切成多 task, 各 `skein create` 登记, task 级 `--deps` 串成互依赖 DAG (契约/基础 task 先)。原归一 task 作废或改造为其中一个。
- **用户选不拆** → 归一继续。
- 阈值 8 是启发默认 (ponytail: 拍脑袋定, 明显偏离再调), 边界模糊仍以 `AskUserQuestion` 用户裁定为准。

## 流程

**🛑 plan/confirm 不受 deps 完成状态阻塞 (仅 `skein start` 受限)** — `skein create`/`deps`/`confirm` 均不查前置完成状态, 仅 `skein start` 才查 (脚本硬拒未完成 deps)。pending task 不论前置是否 plan/finish, 照常走完整流程推到就绪, 等 `skein start` 时才等前置。

1. **判新旧 + 定粒度** — 全新任务 vs 对现有 active task 的补充/延续。不准 → `AskUserQuestion` 用户裁定。并入现有 → 更新其工件 + `subtask add`, 不新建。
   - **登记前强制先查未完成 task (硬前置)** — 任何 `create` 之前 MUST 先 `skein list --status open --json | jq -c '[.[] | {id,name,desc}]'` 核对: 新请求与在列某 task **相关** (同目标/同模块/共享改动面/互为前置) → **并入该 task 补 subtask, 禁新建**; 无相关项才 `create`。**禁不查就 create、禁一直堆新 task** (散 task 丢共享上下文一致性, 头号反模式)。
   - **🧭 模糊信号判据 (命中即 cold-start, 进愿景翻译; 不命中走常规 brainstorm, 零增量)** — 用户输入任一命中: ① 无动词或动词泛 ("重构/优化/加能力"无宾语); ② 无文件路径 / 无具体模块名; ③ 一句话 <15 字; ④ 愿景腔 → 标 cold-start。命中零条 = 清晰输入, 跳过愿景翻译直接常规 brainstorm。
   - **归一 vs 分立按相关性, 非按「可独立验收」** — 新交付物与现有 active task 或本请求内其他交付物**相关** → **优先归一 task 拆 subtask**, 禁另开多 task。仅当目标独立、无共享改动面、无依赖 → 才拆多 task。
   - 默认**倾向归一** —— 相关工作散成多 task 会丢共享上下文一致性, 归一拆 subtask 才守住。
2. **登记** — 全新 → `skein create <id> --name <标题> --desc <一句话> [--deps ..]` (`<id>`/`--name`/`--desc` 三者必填), `<id>` 须为**可读描述性 slug** (kebab-case, 如 `order-create-api`), **禁 `t01`/`t2` 字母+数字代号** (脚本硬拒)。得工件目录。
3. **brainstorm 需求/方案** (main 交互式) — 逐问澄清: 目标 / 用户价值 / 边界 / 非目标 / 验收基准 / 方案取舍。禁 main 自行凭空设计。用 `AskUserQuestion` 拍板关键分歧。提问法内置 relentless interview 纪律 (插件内闭环, 原生自足; 装了 ask-matt `/grill-with-docs` / `/grill-me` 可选增强): 一次一问等反馈、每问带 2-3 推荐答案让用户裁、事实自查 (Read/Grep)、决策交用户、共识才放行。
   - **🛑 findings.md 由 researcher 边研边增量写 (调研才生)** — researcher 每完成一主题即把收敛结论追加进 `findings.md`, research/ 存过程证据。main 收 researcher 回传后**只读 findings.md 做跨主题复核/补漏, 不重读 research/**。findings.md = 调研最终交付物; 未调研则 **findings.md/research/ 均不产出** (create 也不预建空壳)。
   - **🧭 愿景翻译 (cold-start 命中才跑; 清晰输入跳过, 零增量)**:
     - **Job Story 三段草拟** — main 套用户原话填 "When [情境], I want [动机], so I can [预期成果]", `AskUserQuestion` 让用户确认/修正三段, 锁定 outcome 再谈 solution。
     - **said / implied / missing 三分** — **明说**的入正文; **暗示**的入正文并回读确认; **缺失**的逐条列 prd.md「Open Questions」用 `AskUserQuestion` 问 (≤3 轮, 超限标「需求未定」停 planning); main 的**假设**强制写 prd.md「Assumptions」段, 禁埋正文 (防 Assumption Burial)。
     - **产物** — 「愿景 (Job Story)」+「Open Questions」+「Assumptions」段写入 prd.md; 收敛后接常规 brainstorm 补目标/边界/验收。
   - **🧭 supertask 创建时机 (cold-start 收敛后判, 默认不建)** — 愿景翻译收敛后, 若需求过大需拆多个**各自完整 plan/exec/check/finish** 的独立小需求 → 建 supertask (`skein create <super-id> --kind supertask`) 作聚合层, 各小需求 `skein create <child-id> --parent <super-id>` 作 child task (深度限 2 层)。**单 task 可覆盖的中小需求** → 不建 supertask。
4. 🛑 **grill 硬门 (未过禁进 exec · STOP)** — 委托 `skein-grill` 全轴对抗校对, 重点确认「用户想法 = PRD 写的」。弱点表交用户过, 补齐后放行。**未跑 grill 禁进 exec**; grill 未完成或弱点表未补齐 → 停在本步, 禁推进。
   - **锁定契约** — grill/brainstorm 里梳理出的不变量 (MUST/禁/边界条件) 由 main 用脚本逐条锁进 task.json (main 同步跑脚本, 不派 agent):
     - `skein contract <id> --add "契约文本"` (每条一次) / `skein contract <id>` (列出核对)
5. **产出工件** — `create` 落 prd/design 双脚手架 (本步填正文); 调度落 task.json (脚本):
   - `prd.md` (主入口) — 分章节: **目标 / 边界 / 验收标准 / 索引**。每章节自带 `- [ ] TODO`, 填完逐个勾掉。**验收标准章例外**: planning 只列全、**保持 `- [ ]` 未勾** (勾选归 check 阶段验证通过后回写)。**prd 章节内容经脚本写, 禁裸 Edit prd.md**: `skein prd write <id> --type={目标|goal|边界|scope|验收标准|acceptance} --list "<多行文本>"` / `skein prd add` (追加) / `skein prd check <id> --type=acceptance --list "<条目>"` (勾选)。
   - `design.md` — 详细设计: 架构 / 数据流 / 取舍 / 技术选型 (**不含调度图**) + **可能性分支** section。**写入界限: 仅 planning 阶段写 (含 check 失败回 planning 的二次进入); exec / check / finish 阶段禁动 design.md**。exec/check 发现方案需调整 → 回 planning 改 design 后重派。
     - **当前方案 = 精简守现状 (YAGNI)** — design.md 正文只写满足当前需求的最小可行设计, 禁塞"以后可能要"的扩展点。
     - **可能性分支 section (研究期允许过度探索, 仅留痕)** — 现状之外的扩展方案 / 未来约束变化时的演进分支 / 被否决的备选, 写入「可能性分支」section, 每条**必须标触发条件**。不进最终设计方案正文, 不进 task.json DAG, 不生成 subtask。
     - **deep-module 词表 + ADR**: 设计模块形状 (deep/shallow/seam/depth) + 难逆决策记录见 [references/design-vocabulary.md](references/design-vocabulary.md) (跨子系统/破坏式重构/选型类 task 必用)。
   - **子任务 + 调度 DAG (协议先行, 后并行)** — 拆分铁律: 先把 subtask 间的**共享契约** (接口签名 / 数据结构 / 类型 / 协议格式 / DB schema) 抽成**单个前置 subtask** 优先定死, 下游各实现 subtask 只 `--deps` 这一个契约 subtask、彼此**不互挂依赖** → 契约一 done 即全批并行。每个 subtask 含 depends_on + 验收 checklist, 逐条 `skein subtask add <id> <sid> --name --desc [--agent --deps --check]` 落进 task.json。**这是 exec 唯一调度真值源**, 不写 mermaid 图文件。subtask 拆分 + 依赖登记模板详见 [references/dispatch-graph.md](references/dispatch-graph.md)。
     - **tracer-bullet (端到端瘦实现优先, ask-matt 同源)** — 契约 subtask 本身该是**端到端穿通的最瘦实现** (各层 stub / 空实现但全链路跑通一个 happy path): 第一个 subtask 完成后能验证「整条路走得通」, 再逐 subtask flesh 内部逻辑。早一个周期发现协议缺陷, 是压 makespan 的第二命门。
     - **拆完对表复杂度天花板 (硬)** — subtask 落完立刻对天花板表逐项核。
6. **异步派 skein-dedup (fire-and-forget, 不阻塞 exec)** — 所有 task planning 完成 (batch 末 / plan 收尾, exec 触发前), main **异步派 `skein-dedup`** subagent 全量扫一次未完成 task: ① 查重归并 (自动 `subtask add` 迁入主 task + `skein del` 次 task); ② 给散落的相关 task 补执行序织成完整 DAG (自动 `skein deps`, **仅对现无 deps 的 pending task 补前置, 已有 deps 的不碰**)。**异步不阻塞**: dedup 后台跑, exec 照常推进。
7. **出口 (按路由分流)** — 完成判据勾满后:
   - **flow (缺省 / 任务描述)** → `skein confirm` 转就绪, **直接续 exec 阶段**, 禁停手问用户要不要执行。
   - **显式 `plan`** → 停在 `skein start` 前, 提示用户 `/skein-flow exec <task>` 激活。

## ✅ plan 阶段完成判据 (勾满才转 exec)

- [ ] task 已 `create` (含可读 slug)
- [ ] prd.md 已填完 (目标/边界/索引章 `- [ ] TODO` 全勾; **验收标准章条目列全即可, 保持未勾 — 勾选归 check 阶段**)
- [ ] subtask 已规划 (`subtask add` 落 task.json DAG)
- [ ] 设计方案已定 (design.md 正文; 或 main 判定豁免)
- [ ] 预计工时已填 (`skein estimate <id> --set <小时数>`; `skein confirm` 硬校验非空正数, 规则详见 [references/estimate-gate.md](references/estimate-gate.md))

未勾满 = planning 未收敛, 禁 `skein start` / 禁转 exec。`skein confirm` 亦会逐项硬拒 (subtask/prd/预计工时任一缺失即报错阻断)。

## plan 失败模式

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| brainstorm 用户答不出关键分歧 | 给 2-3 推荐选项让用户选 (非开放式问) | 仍答不出 → 标「需求未定」, 停在 planning, 禁 start |
| grill 弱点表 >3 轮不收敛 | 归并同源弱点, 一次批量 `AskUserQuestion` 裁完 | 仍发散 → scope 过大, 拆多 task (heavy 档 + depends_on) |
| subtask 粒度不清 / 无从定 depends_on | 回 brainstorm 补边界, 按可独立验收切 | 仍切不动 → 派 `skein-researcher` 勘察代码再拆 |

---

# exec 阶段 (执行编排调度门)

只管执行编排 (职责划分 / 并行 / 依赖), 不碰需求 / 方案设计 (那归 plan)。

## 入口路由 (作命令时)

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

## 调度门 (载体分工)

> **工作目录 (worktree 态自适应)** — 详见 [references/worktree-convention.md](references/worktree-convention.md)。真值一律以 task 的 `worktree` 字段为准 (null=原地)。

main 作调度器编排, 改动落各 subtask 工作目录、每个 agent 完成即回传:

- **🛑 subtask 状态先行 (硬前置)** — 详见 [references/state-before-action.md](references/state-before-action.md) 硬门 2。claim 占槽是派 agent 的硬前置, pending/failed 态 subtask 禁直接派 agent。
- **claim 默认即改态占槽 (整批标 running), 无需额外参数; --dry-run 才只读预览**。**调度** → main 亲跑: `skein claim` (**全局跨 task**, 所有 active task ready subtask 合池竞争同一 `max_parallel` 槽) 算就绪批 + 标 running, main 逐个真实 `Agent` 调用 dispatch。批量推进用 `claim`; 单 task 场景用 `skein subtask claim <tid>` 兼容; 预览用 `skein claim --dry-run`。
- **执行** → 派合适 agent (无则 `skein-executor`) 各做 1 subtask, 共享该 task 工作目录, 不调度不递归 (Recursion Guard)。
- **禁 main 亲改源码** — 实质产出一律派 subagent (仅 ≤3 文件微改等特别情况例外, 且必在该 task 工作目录内)。
- **载体 = 单 subagent (禁 team)** — agent-teams 已被 SessionStart 关闭, 需多 agent 协同的活一律拆成独立 subtask 各派单 subagent。
- **及早退出** — 每个载体只做本 subtask、产出即回传**立即退出**, 禁滞留空转。main 侧 `done` 后即 `claim` 放行下游, 全部 done 立即收束进 check。

## 调度循环 (动态, 完成即派)

```
while skein claim 返回非空:       # 全局跨 task 合池竞争 max_parallel 槽
    对认领到的每个 (task, subtask): 为其选合适 agent 真实 Agent 调用
    等任一 subagent 返回
    → skein subtask done/fail <tid> <sid> → 回到 skein claim (完成即派)
```

- **🟢 subtask 调度优先, 空闲才提前 plan (禁干等)** — 详见 [references/dag-scheduling.md](references/dag-scheduling.md) 第 6 节。优先级: 有可调度 subtask → 一律先 `claim` 派 subtask, plan-ahead 是次级填充器必须让位 subtask。
- **🔴 exec 无验收 (完成即 done, 验收全归 check)** — subagent 回传即执行完成, main **只 `done`/`fail`, 禁 exec 阶段勾验收**。exec 只判「执行有没有跑完/报错」, 不判「验收过没过」。
- **并行只看 depends_on DAG / 并发上限 2 / 完成即派** — 详见 [references/dag-scheduling.md](references/dag-scheduling.md)。任一返回即 `done` 后再 `claim`, 不等一批跑完。
- **返回 `需要:` / 阻塞 → 不计 done** — 该 subtask 未完成, 下游保持未 ready; main 转达用户/补信息后重派。
- **🔴 tight feedback loop (先复现再修, ask-matt 同源)** — subtask 失败/报错, **禁直接盲改**: 先建**一条就红的复现命令/最小测试**固定症状, 再读根因修。无复现 = 修了也无法验证, 是猜。自愈重派前 dispatch prompt MUST 含「先复现」指令。
- **subtask 失败 → 自愈闭环 (禁失败即停摆)** — 详见 [references/subtask-operations.md](references/subtask-operations.md) 第 3 节。二选一 (均在本 task scope 内): ① 定点小缺陷 → 原地重派 ≤2 轮; ② 根因是独立可修单元 → 插修复 subtask 定点修根因后重派。兜底: 修复也失败/累计无进展超上限/根因超 scope → 停回传 (走 root-cause-protocol 或转人工)。禁跳过该 subtask 放行下游。
- **exec 中发现独立新问题 → 自主拆新 task, 禁扩当前 scope** — 与自愈**互斥分流**: 自愈修的是**本 task scope 内**失败的 subtask; 本条是暴露**超出本 task 边界**的问题, main 自主走 plan 阶段 / `skein create` 登记为**新排队 task**, 禁塞进当前 task 扩范围。判据: 修复动作是否属原 subtask 目标 —— 属 → 自愈; 不属 → 拆新 task。

## ⚠️ exec 两条硬规

- **异步等待 MUST 输出任务清单** — 派出异步任务后、结束本回合前, 输出全景表: 4 列 id/状态/摘要/进度% (状态枚举 进行中/等待中/阻塞), 例 `| st1 | 进行中 | 改 auth 中间件 | 60 |`。同步前台阻塞 / 无在跑任务不触发。
- **exec 阶段禁问用户顺序** — 顺序归 planning (task.json 子任务 DAG + depends_on)。task.json 缺子任务 DAG → 退回 planning 补, **不在 exec 问**。

## exec 失败模式

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| subtask 报错 (非阻塞) | 自愈: 定点重派 ≤2 轮 / 根因独立则插修复 subtask | 修复也失败/超 scope → 停调度回传 main (走 root-cause-protocol), 禁跳过下游 |
| subagent 返回 `需要:` | main 转达用户 / 补信息后重派 | 信息仍缺 → 该 subtask 挂起, 下游保持未 ready, 禁标 done |
| `claim` 返回空 (满槽 / 无就绪) | 找 `待处理` 且无 subtask 的 task 提前 plan 填空闲 | 满槽等回传; 全 pending 有 subtask 但 `claim` 仍空 → 查 depends_on 死锁 (环) → 停手回 plan 改 DAG |

---

# check 阶段 (质量验证门)

exec 完成后、finish 前的**质量门**。**验证与修复分离**: `skein-checker` 只验证 (无写权), 失败交合适 agent 修。未过禁 finish。

**禁动 design.md** — design.md 写入归 planning (仅 planning 阶段 + check 失败回 planning 二次进入可写); **exec / check / finish 阶段均禁动**。check 检出方案性冲突 → 回 planning 改 design 后重派。

**🛑 check 状态先行 (硬前置)** — 必须先 `skein check <id>` 进检查中态才派 skein-checker 跑验证, 禁 main 在 task 仍「进行中」态自跑验证当 check 结果。

## 流程

1. **验证** — 派 `skein-checker`: 传 Active task id + 工作目录 (task 的 `worktree` 字段; null=原地仓库根)。checker 分两步: **① checkpoint 核对 → ② 场景自适应内置 check**, 回传报告。
   - **① checkpoint 核对 (task + subtask 双层)** — checker 核对本 task 全部 checkpoint:
     - **task 级** — 自跑 `skein prd read <id> --type=acceptance` 取 prd `## 验收标准`, **只验未勾 (`- [ ]`) 项**; 已 `- [x]` 项跳过。
     - **subtask 级** — 逐个 subtask 核对其 planning 登记的 `--check` 验收 checklist (`skein subtask list <id>`)。
   - **② 场景自适应内置 check** — checker 按项目场景自判跑对应内置检查 (多特征并存跑命中的多类):
     - **编程类** — build / test / lint / type-check / **架构一致性** + 契约合规。
     - **小说 / 内容类** — **逻辑一致性** + 设定一致性 + 伏笔呼应。
     - **数据 / ETL 类** — schema 校验 / 数据管道跑通 / 字段一致性 / 样本抽检。
     - **文档 / 知识类** — 链接有效性 / 结构完整 / 术语一致 / 交叉引用不断裂。
     - **配置 / 基建类** — 配置语法校验 / 幂等性 / dry-run / 依赖版本锁一致。
     - **设计 / 前端类** — 组件渲染 / 可访问性 / 视觉回归 / 响应式断点。
     - 无识别场景 → 该项标 `[工具失败: 未识别项目场景]`。
   - **契约逐条验证** — checker MUST 先读出本 task 全部契约, **逐条核对是否被满足**, 报告每条 pass/fail: `skein contract <id>`。任一条 fail → 进修复循环。
   - **一致性核查** — checker MUST 检 subtask 产物间 + 与 prd 契约有无冲突: 接口签名对不上 / 重复实现同一职责 / 命名与约定相斥 / 数据流断裂 / 契约互相矛盾。逐条报冲突对 (哪两处 file:line + 冲突点)。
2. **判定** — 全绿 (含零冲突) → 放行 finish。FAIL 或**检出冲突** → 进修复循环。**本轮验证通过的验收项**, main 经 `skein prd check <id> --type=acceptance --list "<验收项文本>"` 回写勾选态持久化 (脚本写盘, 禁裸 Edit prd.md), 未过项保持 `- [ ]` 留待修复后重验。需反勾用 `skein prd uncheck`。
3. **回 planning 重确认 (复用现有 `进行中` 态)** — 通用回退流程详见 [references/rollback-protocol.md](references/rollback-protocol.md)；check 修复 subtask 操作规范详见 [references/subtask-operations.md](references/subtask-operations.md) 第 4 节。check FAIL 或检出冲突, **禁改 task 状态** (依旧 `进行中`)。main 先回 planning 思维重审失败, 用 `AskUserQuestion` 或 grill 与用户确认修复方向, **禁跳过确认直接补 subtask 回 exec**。check 阶段特有分档:
   - **孤立失败** (单点 lint/type/test/契约 fail) → 确认后加 1 个定点修复 subtask (--deps 挂失败源)。
   - **一致性冲突 / 根因跨 subtask** → 确认后按冲突根因加**多个**修复 subtask (一冲突一 subtask)。**直到全绿且零冲突才放行**。
   - **方案性 / 设计缺陷** (架构选型不对 / 契约定义有误 / 需求边界漏了) → 回 planning **补充或重设计 design.md** (二次进入才可写), 同步修 prd + 改契约, 再据新设计重拆或补子任务。**新方案经 grill/AskUserQuestion 确认无误, 才回 exec**。
   - 方向确认=必经门: main 不得凭报原文擅自加 subtask, 必先 grill/AskUserQuestion 让用户对修复方向拍板。
4. **重验** — 修复 subtask 全 done 后重派 `skein-checker` 复跑 (含一致性)。未过回 planning 重确认循环。
5. **放行** — 全绿且零冲突 → 进 finish 阶段。

## ✅ check 完成判据 (放行 finish 前勾满)

- [ ] checkpoint 核对: task 验收标准 + 各 subtask `--check` 项全完成
- [ ] 场景内置 check 全绿
- [ ] 契约逐条 pass (`skein contract` 全覆盖)
- [ ] 一致性核查零冲突
- [ ] 本轮通过的验收项已回写 `- [x]`

## check 失败模式

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| 孤立失败 (单点 lint/type/test/契约 fail) | 回 planning 重确认: grill/AskUserQuestion 敲定修复方向, 同 task `subtask add` 1 个定点修复子任务 (--deps 失败源), task 保持 `进行中` | 反复不过 → 见下「≥3 轮」路径 |
| 一致性冲突 / 根因跨 subtask | 同 task `subtask add` 多个修复子任务 (一冲突一 subtask), 逐条覆盖 | 冲突未全覆盖禁 finish |
| 修复子任务 ≥2 轮仍 FAIL (第 3 轮) | 停加子任务循环 → 按 [references/root-cause-protocol.md](references/root-cause-protocol.md) 5 维根因复盘 | 带根因回 planning 重确认定向重修; 根因超 exec (需求/设计缺陷) → 停手附根因报告转人工 |

---

# finish 阶段 (收尾闭环门)

check 全绿后的**收尾门**。验收/完成度核对已在 check 阶段做完, **finish 只做收尾** (勘察改动+悬挂 → 合并 → 销 worktree → 标记完成 → 异步 spec), 不重做验收。**未 finish 闭环(标记完成) = 未闭环, 禁宣告 Done。** 归档 = 保留期 (默认 7 天) 到期后 `_autoclean` 自动目录迁移, 非 finish 步、非 Done 门。

## 载体分工

| 动作 | 谁 | 产出 |
|---|---|---|
| 收尾勘察 | 派 `skein-finisher` (只读, 合并前清障) | diff 摘要 + 悬挂清单 (不做验收核对) |
| 清悬挂 + 生命周期 | main 同步跑 (不算实质工作) | `TaskList`/`TaskStop` + `skein finish` (commit→merge→销 worktree→标记完成) |
| sediment 沉淀 | **异步 fire-and-forget** 派 `skein-specer` (finish 闭环后) | specer 自主跑判定门 + `skein-spec sediment` 写盘 + reindex (main 不等回传) |

## 流程

1. **收尾勘察 (合并前清障)** — 输入 `task id + 工作目录` → 派 `skein-finisher` → 出口: diff 摘要 + 悬挂清单。**只勘察改动+悬挂残留供干净合并, 不做验收/subtask 完成度核对 (那是 check 的职责, 到此已全绿)**。悬挂残留 (调试码/临时文件) 由 main 清理后再合并。
2. **清悬挂** — `TaskList` 查残留 subagent / 后台任务 → `TaskStop` 关闭。未关 = 未闭环, 禁 finish。
3. **标记完成 (闭环)** — `skein finish <id>` (commit→merge→销 worktree→标记完成, status=已完成)。**finish 到此即闭环, 禁为 sediment 阻塞**。归档不在此步 (保留期后自动)。
4. **sediment (异步 fire-and-forget)** — finish 闭环后异步派 `skein-specer`, main 不等回传即结束回合。细节见 [references/sediment-protocol.md](references/sediment-protocol.md)。
5. **auto-fix 双保险 (异步 fire-and-forget)** — sediment 派出后, main 检测 `.skein/spec/.pending-fix` 标记 (Stop hook 回合结束若检出 spec 问题所写, 详见 skein-spec auto-fix 模式)。标记存在 → 异步 bg 派 `skein-specer` 跑 `skein-spec maintain --apply` 全自动修, 与 sediment 同批 fire-and-forget。标记不存在 → 跳过。

## ✅ finish 完成判据 (勾满才算闭环)

- [ ] finisher 勘察回传, 悬挂残留已清 (调试码/临时文件)
- [ ] 悬挂 subagent 全 `TaskStop` 关闭
- [ ] `skein finish` 成功 (commit→merge→销 worktree→标记完成)
- [ ] sediment 已异步派出 (不等回传)
- [ ] `.pending-fix` 标记已检测 (有则 auto-fix bg 已派, 无则跳过)

## finish 失败模式

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| finisher 报悬挂残留 | main 清理后再合并 | 清不掉 → 停手, 报用户裁 |
| `skein finish` merge 冲突 | 读冲突文件手动解 → 重跑 finish | 解不开 → 停手, 保留 worktree, 报用户裁 (5 步纪律见 [references/merge-conflict-resolution.md](references/merge-conflict-resolution.md)) |
| auto_commit=false 且有未提交改动 → finish 拒绝 | 提示用户手动 `git commit` 后重跑 finish | 用户不提交 → 停手, 禁 --force 强删 (会丢改动) |
| 悬挂 subagent `TaskStop` 关不掉 | 重试 `TaskStop` | 仍在 → 停手, 禁 finish (未闭环) |

---

# 通用部分 (全阶段适用)

## 闭环完成判据 (四步逐一勾满才算 Done)

- [ ] plan: 查重 + create/并入 + brainstorm 需求澄清 + grill 确认 + `skein confirm` (待处理→就绪) + `skein start` 激活
- [ ] exec: 每 ready subtask 派真实 `Agent`, 回合末输出任务清单
- [ ] check: lint/type/test/契约全绿且零冲突
- [ ] finish: merge + 销 worktree + 标记完成 (检查中→已完成) + sediment 异步派出

## 作用域边界 (何时建 task)

**原则: 该走 flow 的直接走, 不问用户要不要走; 简单的直接做, 不问能不能 inline。能走 flow 还是 inline 是 AI 自己该判的选择, 禁抛给用户。**

| 特征 | 判定 |
|---|---|
| 纯查询 / 文档阅读 / 问答 (无改动) | 豁免 (直接做) |
| 单文件单处改, ≤20 行且位置已知 | 豁免 (直接做) |
| 跨 ≥2 文件 / 单文件多处 / 多步骤 | **必建 task (直接走 flow)** |
| 需外部调研 / 产出文档交付 | **必建 task (直接走 flow)** |
| 边界模糊 (走 flow vs inline 难判) | AskUserQuestion 问用户 (禁自行 inline 蒙混) |

归一 vs 分立 / worktree 豁免 / 完成判定 详见 [references/scope-boundary.md](references/scope-boundary.md)。

## 🧭 场景路由 (ask-matt 同源)

决定建 task 后, 按**输入场景**定 planning 力度与走法:

| 场景信号 | skein 内置走法 |
|---|---|
| **新 idea / 新功能 (有 codebase)** | 常规 plan→exec→check→finish; plan 跑 grill 硬门 + research 判定门 |
| **雾区大需求 (跨子系统 / 破坏式重构 / 看不清全貌)** | heavy 档: 强化 grill + research 判定门保守灰区自动派 researcher + 命中复杂度天花板拆多 task |
| **bug 堆积 / 多 issue 涌入** | plan 登记前查未完成 task (查重归并) + plan 收尾异步派 skein-dedup 织 DAG |
| **难 bug 反复 (一处崩全批停)** | exec subtask 失败自愈闭环; check 根因协议兜底 |
| **代码健康 / 架构改进 (非 feature)** | 独立 `skein create` 改进类 task, 走标准四步闭环 |
| **设计问题需验证 (UI/状态模型)** | plan research 判定门派 skein-researcher 勘察, 或独立 sandbox task 原型验证 (不落主仓库) |
| **多 session 大型 build** | supertask 聚合层 + child task 各自完整闭环, task 级 `--deps` 排队 |

**零外部 skill 硬依赖** — skein 四步闭环自包含覆盖全部场景。熟悉 Matt Pocock `/ask-matt` 套件者, 完整 skill 级映射见 [references/matt-pocock-mapping.md](references/matt-pocock-mapping.md)。

## 失败模式 (全阶段通用)

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| 判新旧不准 (新建 vs 并入现有 active) | `AskUserQuestion` 用户裁定 | 用户也不确定 → 默认新建, 保守留旧 task 不动 |
| 相关工作误判成独立 (拆多 task) | 按相关性收敛: 相关 → 归一 task 拆 subtask (`subtask add`) | 已误建多 task → `skein archive <多余task-id>` 归档多余者 |
| 某阶段未达出口 (plan 未收敛 / check 未绿) | 停在该阶段, 禁跨阶段推进 | 反复不过 → 走对应阶段兜底 (check 第 3 轮根因复盘) |
| 宣称派 agent 但无 `Agent` tool_use | 立即在同回合补真实 `Agent` 调用 | 补不出 → 硬错停手, 禁回传「已派出 / 在做」 |
| 有 subtask 却想 inline 顺跑 | 停手, 走 exec `claim→派 Agent` 循环 | 派不出 → 硬错停手, 禁 main 代跑 subtask |
| 第二个 flow 进来, 第一个还没 durable | 先给第一个 `skein create` 落盘再处理第二个 | 都未落盘 → 立即各自 `create`, 未处理者留 pending 待续 |

## ✅ 正向配方 (命中反面=流程错误)

> 🔒 铁律: 「派 agent」=真实 `Agent` tool_use — 无 tool_use 即没派, 禁回传「已派出」。

| 场景 | 正确做法 (❌ 反面) |
|---|---|
| 改动源码 | 派 agent 在 task worktree 内改 (❌ main 直接改源码 / 无 worktree 改源码) |
| 处理请求 | 强制走 task 闭环, 即使看似简单 (❌ inline 跳 task) |
| 派 agent 声明 | 必带真实 `Agent` tool_use, 无则硬错停手禁回传 (❌ 宣称派 agent 无 tool_use) |
| 改任务状态 | 经 skein CLI 操作 (❌ 直编 `.skein/task.md`) |
| 用户确认 / 选择 | 走 AskUserQuestion 工具 (❌ 纯文本代替) |
| exec 派发顺序 | 按 depends_on DAG 自动排序即派 (❌ exec 阶段问用户顺序) |
| 有 subtask 的 task | 走 claim→派 subagent→done 循环 (❌ main inline 顺跑不派 subagent) |
| 新 flow 进来 / 多请求 | 先给在飞的第一个 task durable 落盘再处理第二个 (❌ 第二个 flow 顶掉在飞 task) |
| 相关工作组织 | 归一 task 拆 subtask (❌ 相关工作拆成多个 task) |
| brainstorm 载体 | main 亲做交互式对话 (❌ 派 subagent 做 brainstorm — 它不能问用户) |
| 进 exec 前置 | 先过 grill 硬门再推进 (❌ 跳 grill 硬门进 exec) |
| 调度图/子任务落盘 | 写进 task.json (❌ 写进 md 文件) |
| subagent 回传后 (exec) | 只 `subtask done/fail` (❌ exec 阶段勾验收 — 归 check) |
| 跑验证 (check) | 派 `skein-checker` (❌ main 亲跑 lint/test) |
| checker 报失败 | 交合适修复 agent 定点改 (❌ checker 自改码) |
| check 失败 | 走回 planning 重确认: grill 敲定方向 → 同 task `subtask add`, task 保持 `进行中` (❌ 跳确认补 subtask / 改状态 / 另建 task) |
| 收尾勘察 | 派 `skein-finisher` 做勘察 (❌ main 亲跑收尾勘察) |
| finisher 职责 | finisher 只读勘察改动+悬挂, 不做验收核对 (❌ finisher 核对 subtask 完成度 / 自己改码 / 跑 sediment) |
| sediment 时序 | finish 先闭环, sediment 异步 fire-and-forget 在后 (❌ sediment 阻塞 finish) |
| 宣告 Done | `skein finish` 标记完成后才宣告 Done (❌ 未 finish 闭环即宣告 Done) |
