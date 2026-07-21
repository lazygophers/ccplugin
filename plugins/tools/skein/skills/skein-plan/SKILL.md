---
name: skein-plan
description: planning 入口 + 单一真值源 (用户显式 /skein-plan 或被 skein-flow 委托)。新建 SKEIN task 做需求梳理: 判新旧 + create 登记 + 交互式 brainstorm + grill 硬门。产出 prd.md + design.md + 子任务/依赖 DAG 落 task.json。无参 = 停在 start 前 (只规划不执行); --continue = 返回工件路径供 flow 激活。
user-invocable: true
argument-hint: "[任务描述]"
arguments: "[任务描述]"
model: opus
effort: high
---

# skein-plan — planning 入口 + 单一真值源

**planning 单一真值源**。判新旧 + 登记 + brainstorm + grill, 产出 planning 工件。**全程 main 同步前台** — brainstorm/grill 需逐问用户 (`AskUserQuestion`), subagent 不能与用户对话, 故不派执行 subagent (纯信息调研按下方「research 判定门」决定是否派 `skein-researcher` 只读 subagent, 设计决策 main 汇总裁定)。

## 🧭 research 判定门 (自动判, 非用户说要才派)

brainstorm 前先定**是否需要派 skein-researcher**, 按信号分档自动判 (非 main 临场感觉, 非等用户说):

| 档 | 信号 | 判定 |
| --- | --- | --- |
| **明确需** | 外部 API / 库选型 / 跨陌生子系统 / 现状代码未知 / 协议待定 | **自动派 researcher** |
| **明确不需** | 已知代码模式 / 用户给足信息 / 单熟悉子系统 / 单点改 | **跳 research, 直 brainstorm** |
| **保守灰区** | 倾向需但不明确 (可能涉未知但不确定) | **自动派 researcher** (宁可调研) |
| **激进灰区** | 倾向不需但拿不准 (看似简单但可能有坑) | **AskUserQuestion 问用户是否需 research** |
| **兜底** | brainstorm 中 subtask 切不动 / depends_on 定不了 | **触发派 researcher** 勘察代码再拆 |

派 researcher 后仍受「探索封顶」约束 — 够拆 subtask 即收敛, 禁无限深挖。

`skein-researcher` 的结论持久化在 `.skein/task/<id>/research/` (dispatch 时把该 task id 作为 task-id 传给它)。planning 后续步骤 (brainstorm/PRD) 可复读这些笔记, 不必只靠回传摘要或记忆; task finish 归档时随 task 目录一并归档。

**探索封顶, 尽早转异步 (禁无休止调研)** — 登记 task 后目标是**尽快填好 prd + subtask DAG 就转 exec 异步并行执行**, 不是把时间耗在调研上。调研**够用即停**: 只查够拆出 subtask + 定依赖所需的信息 (选型/边界/接口), 达到能拆分即收敛, 禁为求完备无限深挖。拿不准的细节留成 subtask 的验收条或 `需要:` 交执行阶段解决, 而非 planning 阶段一次探完。**能并行的尽早并行** — 早拆早派早完成, 是最短工期的前提。

**🧠 smart zone / context hygiene (ask-matt 同源)** — grill→prd→subtask DAG 三步应在**同一不中断 context window** 内完成 (中途不 compact), 保持思考连贯: grill 撑锐的需求直落 prd, prd 的边界直落 subtask 拆分, 一气呵成。接近 smart zone (~120k token) 上限 → 先收敛: 派 `skein-researcher` 异步卸载调研 / 把已收敛结论压进 prd.md/design.md 工件 (工件即跨 context 持久态) → 腾出窗口继续, **禁 degraded 状态硬推** (degraded 拆出的 subtask 质量不可靠)。

## 入参 (决定是否停在 start 前)

- **无参** (用户直呼 `/skein-plan`) → 跑完 planning **停在 start 前**, task 留 planning 态, 交还控制权。**禁 `skein start` / 禁 exec / check / finish** — 执行归 `skein-flow` / `/skein-exec`。
- `--continue` (skein-flow 委托) → 跑完 planning **不停**, 返回工件路径 (供 `skein-flow` 自接激活)。

## 策略分档 (轻量路由启发)

判新旧后先给任务定档, 决定 planning 力度 (**仅路由启发, 非新增机器/字段**):

| 档           | 判据                                 | 走法                                                                                                                                   |
| ------------ | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| `direct-fix` | 单点微改, 在作用域边界表豁免范围内   | 不建 task, 直接改                                                                                                                      |
| `standard`   | 跨文件 / 多步, 单 task 可覆盖        | 常规 plan→exec→check→finish                                                                                                            |
| `heavy`      | 跨子系统 / 破坏式重构 / 多 task 并行 | 强化 grill + 可能拆多 task + 显式 `depends_on`。破坏式重构 (改契约/删旧路径/全站点一次改齐, 禁垫片) 见 references/breaking-refactor.md |

### 🛑 复杂度天花板 (归一有上限, 命中必提醒用户拆多 task)

归一是默认, 但**单 task 有复杂度天花板** —— 不是相关工作就无脑塞进一个 task 让它执行完所有事。planning 拆完 subtask 后 (subtask 数已知) 逐项对表, **命中任一即停下**, 用 `AskUserQuestion` 提醒用户「本 task 过复杂, 建议拆成多个互相依赖的 task」:

| 天花板信号             | 判据                                                                 |
| ---------------------- | -------------------------------------------------------------------- |
| subtask 数超阈值       | 拆出 subtask **> 8** (或 brainstorm 已看出会 > 8)                     |
| 跨子系统 / 多改动面    | scope 跨 ≥2 子系统 / 多个独立改动面 (如前端+后端+DB+基建各成一摊)     |
| 工期 / 风险高          | 预估工期长 / 破坏式重构 (heavy 档) / 一处崩全批停                     |

- **用户选拆** → 按子系统 / 改动面切成多 task, 各 `skein create` 登记, 用 **task 级** `--deps` / `skein deps` 串成互依赖 DAG (契约/基础 task 先, 消费方后)。原归一 task 作废或改造为其中一个。
- **用户选不拆** → 归一继续, 照常 `subtask add` 拆 subtask DAG。
- 阈值 8 是启发默认 (ponytail: 拍脑袋定, 明显偏离再调), 非硬机器 —— 边界模糊仍以 `AskUserQuestion` 用户裁定为准。

### 作用域边界 (何时建 task)

| 特征                              | 判定                            |
| --------------------------------- | ------------------------------- |
| 纯查询 / 文档阅读 / 问答 (无改动) | 豁免, 不建 task                 |
| 单文件单处改, ≤20 行且位置已知    | 豁免                            |
| 跨 ≥2 文件 / 单文件多处 / 多步骤  | **必建 task**                   |
| 需外部调研 / 产出文档交付         | **必建 task** (调研走 research) |
| 边界模糊                          | AskUserQuestion 问用户 (禁自行 inline 蒙混) |

## 流程

1. **判新旧 + 定粒度** — 全新任务 vs 对现有 active task 的补充/延续。不准 → `AskUserQuestion` 用户裁定。并入现有 → 更新其工件 + `subtask add`, 不新建。
   - **登记前强制先查未完成 task (硬前置)** — 任何 `create` 之前 MUST 先 `skein list --status open --json` (一次取全部未完成 task 压缩 JSON) 核对: 新请求与在列某 task **相关** (同目标/同模块/共享改动面/互为前置) → **并入该 task 补 subtask, 禁新建**; 无相关项才 `create`。**禁不查就 create、禁一直堆新 task** (散 task 丢共享上下文一致性, 是头号反模式)。
   - **🧭 模糊信号判据 (命中即 cold-start, 进 step 3 愿景翻译; 不命中走常规 brainstorm, 零增量)** — 用户输入任一命中: ① 无动词或动词泛 ("重构/优化/加能力"无宾语); ② 无文件路径 / 无具体模块名; ③ 一句话 <15 字; ④ 愿景腔 ("我有个想法/想做个/感觉") → 标 cold-start。命中零条 = 清晰输入, **跳过愿景翻译直接常规 brainstorm (零增量路径)**。
   - **归一 vs 分立按相关性, 非按「可独立验收」** (subtask 亦可独立验收): 新交付物与现有 active task 或本请求内其他交付物**相关** (同目标 / 同模块 / 共享改动面 / 互为前置) → **优先归一 task 拆 subtask** (`subtask add` + `--deps` 连 subtask 级 DAG), 禁另开多 task。
   - **仅当目标独立、无共享改动面、无依赖** → 才拆多 task (各 `skein create` 登记, task 级 `--deps` 排队 / 无序并行; active 集 ≤ 2 自动排队)。
   - 拆不拆是 planning 自主判断, 边界模糊才 `AskUserQuestion`。默认**倾向归一** —— 相关工作散成多 task 会丢共享上下文一致性 (类型/契约决策各 task 重推), 归一拆 subtask 才守住。
2. **登记** — 全新 → `skein create <id> --name <标题> --desc <一句话> [--deps ..]` (`<id>`/`--name`/`--desc` **三者必填**, 缺一 argparse 报错), `<id>` 须为**可读描述性 slug** (kebab-case, 如 `order-create-api` / `user-auth`; 兼作分支名 + 目录名), **禁 `t01`/`t2` 这类字母+数字代号** (脚本硬拒)。得工件目录。(`create` 自动刷看板)
3. **brainstorm 需求/方案** (main 交互式) — 逐问澄清: 目标 / 用户价值 / 边界 / 非目标 / 验收基准 / 方案取舍。禁 main 自行凭空设计。用 `AskUserQuestion` 拍板关键分歧。提问法内置 relentless interview 纪律 (插件内闭环, 不依赖外部 /grilling / /grill-me): 一次一问等反馈 (仅同源不依赖才批)、每问带 2-3 推荐答案让用户裁、事实自查 (Read/Grep)、决策交用户、共识才放行。
   - **🛑 派 skein-researcher 后必收敛写 findings.md** — researcher 回传后, main 把**跨主题收敛结论**写入 `findings.md` (非整篇搬运 research/): 只写收敛要点 + 关键依据/引用 + 未决项 (`需要:`)。findings.md = 调研最终交付物, research/ = 过程证据。**researcher 不写 findings.md (只提供素材), 收敛归 main** — 未写 findings.md 即 planning 未收敛, 同 prd TODO 未勾。
   - **🧭 愿景翻译 (cold-start 命中才跑; 清晰输入跳过, 零增量)**:
     - **Job Story 三段草拟** — main 套用户原话填 "When [情境], I want [动机], so I can [预期成果]", `AskUserQuestion` 让用户确认/修正三段 (各给 2-3 推荐选项), 锁定 outcome (为谁/为何/价值) 再谈 solution。
     - **said / implied / missing 三分** — **明说**的入正文; **暗示**的入正文并回读确认; **缺失**的逐条列 prd.md「Open Questions」用 `AskUserQuestion` 问 (≤3 轮, 超限标「需求未定」停 planning); main 的**假设**强制写 prd.md「Assumptions」段, 禁埋正文 (防 Assumption Burial)。
     - **产物** — 「愿景 (Job Story)」+「Open Questions」+「Assumptions」段写入 prd.md; 收敛后接常规 brainstorm 补目标/边界/验收。
   - **🧭 supertask 创建时机 (cold-start 收敛后判, 默认不建)** — 愿景翻译收敛后, 若需求过大需拆多个**各自完整 plan/exec/check/finish** 的独立小需求 → 建 supertask (`skein create <super-id> --kind supertask --name --desc`, 占位 st2 实现) 作聚合层, 各小需求 `skein create <child-id> --parent <super-id>` 作 child task (深度限 2 层: supertask→task→subtask, child 不再生 child)。**单 task 可覆盖的中小需求** → 不建 supertask, 走现有 single task 零增量。
4. 🛑 **grill 硬门 (未过禁进 exec · STOP)** — 委托 `skein-grill` 全轴对抗校对, 重点确认「用户想法 = PRD 写的」。弱点表交用户过, 补齐后放行。**未跑 grill 禁进 exec**; grill 未完成或弱点表未补齐 → 停在本步, 禁推进。
   - **锁定契约** — grill/brainstorm 里梳理出的不变量 (MUST/禁/边界条件) 由 main 用脚本逐条锁进 task.json (main 同步跑脚本, 不派 agent), 供 check 阶段逐条验证:
     - `skein contract <id> --add "契约文本"` (每条一次)
     - `skein contract <id>` (列出核对)
     - 例: `contract <id> --add "响应体 MUST 保持向后兼容, 禁删字段"`; `contract <id> --add "单文件改动禁超 200 行"`。
5. **产出工件** — `create` 已落 prd/design/findings 三脚手架 (骨架标题, 本步填正文); 调度落 task.json (脚本):
   - `prd.md` (主入口) — 分章节: **目标 / 边界 / 验收标准 / 索引** (链 design/findings/task.json)。每章节自带 `- [ ] TODO`, 填完逐个勾掉; 未勾清 = planning 未收敛。**prd 章节内容经脚本写, 禁裸 Edit prd.md**: `skein prd write <id> --type={目标|goal|边界|scope|验收标准|acceptance} --list "<多行文本>"` (整章重建) / `skein prd add <id> --type=... --list "..."` (追加) / `skein prd check <id> --type=acceptance --list "<条目文本>"` (勾选, 验收逐条达标即勾)。脚本自动规范化 (目标/验收标准补 `- [ ]`, 边界补 `- `)。
   - `design.md` — 详细设计: 架构 / 数据流 / 取舍 / 技术选型 (**不含调度图**, 调度归 task.json) + **可能性分支** section。**写入界限: 仅 planning 阶段写 (含 check 失败回 planning 的二次进入); exec / check / finish 阶段禁动 design.md**。exec/check 发现方案需调整 → 回 planning 改 design 后重派, 禁就地改。
     - **当前方案 = 精简守现状 (落地不过度设计)** — design.md 正文章节只写满足当前需求的最小可行设计, 禁塞"以后可能要"的扩展点 / 抽象层 / 配置项。YAGNI 在最终设计方案上照常生效。
     - **可能性分支 section (研究期允许过度探索, 仅留痕)** — planning 期鼓励在**研究/探索**环节过度发散: 现状之外的扩展方案 / 未来约束变化时的演进分支 / 被否决但值得留痕的备选, 写入 design.md「可能性分支」section, 用于探究当前方案的合理性边界 (为何这样选 / 换个约束会怎样), 每条**必须标触发条件** (若未来需 X / 若约束变 Y)。**不进最终设计方案正文, 不进 task.json DAG, 不生成 subtask** — exec 阶段只实现「当前方案」精简落地部分。无触发条件的纯臆想仍按 YAGNI 砍。
     - **deep-module 词表 + ADR**: 设计模块形状 (deep/shallow/seam/depth) + 难逆决策记录见 [references/design-vocabulary.md](references/design-vocabulary.md) (ask-matt codebase-design/domain-modeling 同源; 跨子系统/破坏式重构/选型类 task 必用, 简单 task 不勉强)。
   - `findings.md` (需调研时) — 深度调研的收敛结论 + 依据/引用; 过程笔记存 `research/` (researcher 写)。
   - **子任务 + 调度 DAG (协议先行, 后并行)** — 拆分铁律: 先把 subtask 间的**共享契约** (接口签名 / 数据结构 / 类型 / 协议格式 / DB schema) 抽成**单个前置 subtask** 优先定死, 下游各实现 subtask 只 `--deps` 这一个契约 subtask、彼此**不互挂依赖** → 契约一 done 即全批并行。这是压 makespan 的命门 —— 定协议是唯一真串行, 实现全并行。每个 subtask 含 depends_on + 验收 checklist, 逐条 `skein subtask add <id> <sid> --name --desc [--agent --deps --check]` 落进 task.json (sid/--name/--desc 三者必填, `--agent` 省略默认 `skein-executor`)。**这是 exec 唯一调度真值源**, 不写 mermaid 图文件。
     - **tracer-bullet (端到端瘦实现优先, ask-matt 同源)** — 契约 subtask 不止定死接口, 本身该是**端到端穿通的最瘦实现** (各层 stub / 空实现但全链路跑通一个 happy path): 第一个 subtask 完成后能验证「整条路走得通」(协议对得上 / 数据流闭合 / 边界接得上), 再逐 subtask flesh 内部逻辑。这比「定接口→各实现并行→集成时才暴露不通」早一个周期发现协议缺陷, 是压 makespan 的第二命门。
     - **拆完对表复杂度天花板 (硬)** — subtask 落完立刻对「🛑 复杂度天花板」表逐项核: 命中任一 (subtask > 8 / 跨 ≥2 子系统 / 工期风险高) → `AskUserQuestion` 提醒用户拆成多个互依赖 task, 禁默默塞一个 task 执行完所有事。
6. **异步派 skein-dedup (fire-and-forget, 不阻塞 exec)** — 所有 task planning 完成 (batch 末 / plan 收尾, exec 触发前), main **异步派 `skein-dedup`** subagent 全量扫一次未完成 task: ① 查重归并 (同目标 / 同模块 / 共享改动面 / 互为前置, 自动 `subtask add` 迁入主 task + `skein del` 次 task); ② 给散落的相关 task 补执行序织成完整 DAG (自动 `skein deps`, **仅对现无 deps 的 pending task 补前置, 已有 deps 的不碰**, 无关 task 保持孤立)。**异步不阻塞**: dedup 后台跑, exec 照常推进; 归并/补序自动写盘 (CLI 校验存在性/成环)。派它即放手, 不等其回传再 start。
7. **返回** — `--continue` → 返回工件路径给调用方; 无参 → 停在 start 前, 提示用户 `/skein-exec <task>` 或 `/skein-flow` 激活。

## ✅ plan 阶段完成判据 (勾满才转 exec)

- [ ] task 已 `create` (含可读 slug)
- [ ] prd.md 已填完 (各章 `- [ ] TODO` 全勾)
- [ ] subtask 已规划 (`subtask add` 落 task.json DAG)
- [ ] 设计方案已定 (design.md 正文; 或 main 判定豁免 — 简单任务可略)

未勾满 = planning 未收敛, 禁 `skein start` / 禁转 exec。

## 调度 = task.json 子任务 DAG

exec 阶段的 DAG 靠 task.json 的 `subtasks[].depends_on` (经 `skein subtask add --deps` 登记), **非文件里的 mermaid 图**。planning 未登记任何 subtask → `skein start` 硬拒 (无从调度)。subtask 拆分 + 依赖登记模板详见 references/dispatch-graph.md。

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发                                   | 一线修复                                       | 仍失败兜底                                          |
| -------------------------------------- | ---------------------------------------------- | --------------------------------------------------- |
| brainstorm 用户答不出关键分歧          | 给 2-3 推荐选项让用户选 (非开放式问)           | 仍答不出 → 标「需求未定」, 停在 planning, 禁 start   |
| grill 弱点表 >3 轮不收敛               | 归并同源弱点, 一次批量 `AskUserQuestion` 裁完  | 仍发散 → scope 过大, 拆多 task (heavy 档 + depends_on) |
| subtask 粒度不清 / 无从定 depends_on   | 回 brainstorm 补边界, 按可独立验收切           | 仍切不动 → 派 `skein-researcher` 勘察代码再拆        |

## ✅ 正向配方 (命中反面=流程错误)

> 🔒 铁律: 未跑 grill / 未 `subtask add` 任何子任务禁进 exec。

| 场景                     | 正确做法 (❌ 反面)                                                              |
| ------------------------ | ------------------------------------------------------------------------------ |
| 定需求方案               | main brainstorm 逐问用户拍板 (❌ 凭空设计需求方案)                              |
| brainstorm 载体          | main 亲做交互式对话 (❌ 派 subagent 做 brainstorm — 它不能问用户)              |
| 进 exec 前置             | 先过 grill 硬门再推进 (❌ 跳 grill 硬门进 exec)                                 |
| 调度图/子任务落盘        | 写进 task.json (❌ 写进 md 文件)                                                |
| start 前                 | 至少 `subtask add` 一个子任务 (❌ 未 `subtask add` 任何子任务)                  |
| 用户确认/选择            | 用 `AskUserQuestion` (❌ 纯文本代替)                                            |
| 无参调用                 | 停在 start 前只 planning, 执行归 flow/go (❌ 跑 `skein start` 或 exec/check/finish) |
| plan 收尾                | 异步派 skein-dedup 查重织 DAG (❌ 忘派 — 重复 task 漏查归并 / 散 task 丢共享上下文) |
