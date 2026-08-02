# for-plan — plan 阶段作业手册

判新旧 + 登记 + brainstorm + grill, 产出 planning 工件。**全程 main 同步前台** — brainstorm/grill 需逐问用户 (`AskUserQuestion`), subagent 不能与用户对话, 故不派执行 subagent (纯信息调研按下方「research 判定门」决定是否派 `skein-researcher` 只读 subagent)。

## 触发与前置硬门

- **触发**: SKILL.md 参数路由 `$1=plan` (仅规划, 停在就绪) 或 `$1` 缺省/flow (走完整闭环, plan 收敛后自动续 exec)。
- **入口无硬门** — plan 是闭环首阶段, 无前置状态门。
- **出口硬门 = grill (STOP)** — 未过 grill 禁进 exec, 见「流程步骤」第 4 步。

## 流程步骤

### 🧭 research 判定门 (自动判, 非用户说要才派)

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

### 策略分档 (轻量路由启发)

判新旧后先给任务定档, 决定 planning 力度 (**仅路由启发, 非新增机器/字段**):

| 档 | 判据 | 走法 |
|---|---|---|
| `direct-fix` | 单点微改, 在作用域边界表豁免范围内 | 不建 task, 直接改 |
| `standard` | 跨文件 / 多步, 单 task 可覆盖 | 常规 plan→exec→check→finish |
| `heavy` | 跨子系统 / 破坏式重构 / 多 task 并行 | 强化 grill + 可能拆多 task + 显式 `depends_on`。破坏式重构 (改契约/删旧路径/全站点一次改齐, 禁垫片) 须任务显式授权, 否则默认走加固式修补 |

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

### 主流程

**🛑 plan/confirm 不受 deps 完成状态阻塞 (仅 `skein start` 受限)** — `skein create`/`deps`/`confirm` 均不查前置完成状态, 仅 `skein start` 才查 (脚本硬拒未完成 deps)。pending task 不论前置是否 plan/finish, 照常走完整流程推到就绪, 等 `skein start` 时才等前置。

1. **拆诉求 → 逐条判新旧 + 定粒度** — **用户一句话 ≠ 一个 task**。先把请求拆成互不依赖的独立诉求, 再逐条判去向。
   - **诉求数 ≠ task 数**: 一条请求可能对应 1 个 task / N 个 task / 部分并入已有 task + 剩余拆 N 个新 task。**禁默认一句话开一个 task** — 把不相关诉求塞进同一 task 会让 prd 边界糊、验收无法逐条核对、一处卡住全批停。
   - **归一 vs 拆分判据**: 改动面重叠 / 互为前置 / 共享契约 → 归一个 task; 改动面不相交且各自可独立验收 → 拆成各自的 task。拿不准 → `AskUserQuestion` 用户裁定。
   - 逐条诉求各自判「全新 vs 对现有 active task 的补充/延续」。不准 → `AskUserQuestion` 用户裁定。并入现有 → 更新其工件 + `subtask add`, 不新建。
   - **登记前强制先查未完成 task (硬前置)** — 任何 `create` 之前 MUST 先 `skein list --status open --json | jq -c '[.[] | {id,name,desc}]'` 核对: 新请求与在列某 task **相关** (同目标/同模块/共享改动面/互为前置) → **并入该 task 补 subtask, 禁新建**; 无相关项才 `create`。**禁不查就 create、禁一直堆新 task** (散 task 丢共享上下文一致性, 头号反模式)。
   - **🧭 模糊信号判据 (命中即 cold-start, 进愿景翻译; 不命中走常规 brainstorm, 零增量)** — 用户输入任一命中: ① 无动词或动词泛 ("重构/优化/加能力"无宾语); ② 无文件路径 / 无具体模块名; ③ 一句话 <15 字; ④ 愿景腔 → 标 cold-start。命中零条 = 清晰输入, 跳过愿景翻译直接常规 brainstorm。
   - **归一 vs 分立按相关性, 非按「可独立验收」** — 新交付物与现有 active task 或本请求内其他交付物**相关** → **优先归一 task 拆 subtask**, 禁另开多 task。仅当目标独立、无共享改动面、无依赖 → 才拆多 task。
   - 默认**倾向归一** —— 相关工作散成多 task 会丢共享上下文一致性, 归一拆 subtask 才守住。
2. **登记** — 全新 → `skein create <id> --name <标题> --desc <一句话> [--deps ..]` (`<id>`/`--name`/`--desc` 三者必填), `<id>` 须为**可读描述性 slug** (kebab-case, 如 `order-create-api`), **禁 `t01`/`t2` 字母+数字代号** (脚本硬拒)。得工件目录。
3. **brainstorm 需求/方案** (main 交互式) — 逐问澄清: 目标 / 用户价值 / 边界 / 非目标 / 验收基准 / 方案取舍。禁 main 自行凭空设计。用 `AskUserQuestion` 拍板关键分歧。提问法内置 relentless interview 纪律 (插件内闭环, 原生自足; 装了 ask-matt `/grill-with-docs` / `/grill-me` 可选增强): 一次一问等反馈、每问带 2-3 推荐答案让用户裁、事实自查 (Read/Grep)、决策交用户、共识才放行。
   - **🧭 brainstorm 前先拉现状 wiki** — `skein-spec recall "<任务关键词>" --src product` 召回 product namespace 既有现状页, 有命中先读现状再问 (防重复设计已有能力/凭空臆断现状); 无命中视为新功能域, 正常 brainstorm。
   - **🛑 findings.md 由 researcher 边研边增量写 (调研才生)** — researcher 每完成一主题即把收敛结论追加进 `findings.md`, research/ 存过程证据。main 收 researcher 回传后**只读 findings.md 做跨主题复核/补漏, 不重读 research/**。findings.md = 调研最终交付物; 未调研则 **findings.md/research/ 均不产出** (create 也不预建空壳)。
   - **🧭 愿景翻译 (cold-start 命中才跑; 清晰输入跳过, 零增量)**:
     - **Job Story 三段草拟** — main 套用户原话填 "When [情境], I want [动机], so I can [预期成果]", `AskUserQuestion` 让用户确认/修正三段, 锁定 outcome 再谈 solution。
     - **said / implied / missing 三分** — **明说**的入正文; **暗示**的入正文并回读确认; **缺失**的逐条列 prd.md「Open Questions」用 `AskUserQuestion` 问 (≤3 轮, 超限标「需求未定」停 planning); main 的**假设**强制写 prd.md「Assumptions」段, 禁埋正文 (防 Assumption Burial)。
     - **产物** — 「愿景 (Job Story)」+「Open Questions」+「Assumptions」段写入 prd.md; 收敛后接常规 brainstorm 补目标/边界/验收。
   - **🧭 supertask 创建时机 (cold-start 收敛后判, 默认不建)** — 愿景翻译收敛后, 若需求过大需拆多个**各自完整 plan/exec/check/finish** 的独立小需求 → 建 supertask (`skein create <super-id> --kind supertask`) 作聚合层, 各小需求 `skein create <child-id> --parent <super-id>` 作 child task (深度限 2 层)。**单 task 可覆盖的中小需求** → 不建 supertask; 需要在 task 内部拆步骤而非独立闭环 → 用 subtask, 不建新 task。**已存在的 task 事后判定该归某 supertask** → 用 `skein parent <id> --set <super-id>` 改挂 (无需删档重建), `--set ""` 摘除; `parent` 与 `deps` 正交, 改挂不影响既有前置依赖。supertask finish 前要求全部 child 已完成, 否则脚本硬拒。
4. 🛑 **grill 硬门 (未过禁进 exec · STOP)** — 委托 `skein-grill` 全轴对抗校对, 重点确认「用户想法 = PRD 写的」。弱点表交用户过, 补齐后放行。**未跑 grill 禁进 exec**; grill 未完成或弱点表未补齐 → 停在本步, 禁推进。
   - **锁定契约** — grill/brainstorm 里梳理出的不变量 (MUST/禁/边界条件) 由 main 用脚本逐条锁进 task.json (main 同步跑脚本, 不派 agent):
     - `skein contract <id> --add "契约文本"` (每条一次) / `skein contract <id>` (列出核对)
5. **产出工件** — `create` 落 prd/design 双脚手架 (本步填正文); 调度落 task.json (脚本):
   - `prd.md` (主入口) — 标准**六段** (`PRD_SECTIONS_V6`): **目标 / 边界 / User Stories / 验收标准 / Testing Decisions / 索引**。每章节自带 `- [ ] TODO: 填X` 占位, 填写 = 把占位**整行替换**为真实内容, **不是把它勾成 `- [x]`**。**目标/验收标准两章条目 planning 期一律保持 `- [ ]` 未勾** — 勾选权归 check 阶段验证通过后回写, planning 预勾即流程错误。三段 (目标/边界/验收标准) 经脚本写, 禁裸 Edit: `skein prd write <id> --type={目标|goal|边界|scope|验收标准|acceptance} --list "<多行文本>"` (`prd write` 自动完成整行替换) / `skein prd add` (追加) / `skein prd check <id> --type=acceptance --list "<条目>"` (勾选); User Stories / Testing Decisions 两段无脚本 `--type`, 直接 Edit 填正文 (占位整行替换同规则)。旧四段 task 兼容态可用, `confirm` 提示建议迁六段但不硬拦。
   - `design.md` — 详细设计: 架构 / 数据流 / 取舍 / 技术选型 (**不含调度图**) + `## 测试接缝 (seam)` + **可能性分支** section。**写入界限: 仅 planning 阶段写 (含 check 失败回 planning 的二次进入); exec / check / finish 阶段禁动 design.md**。exec/check 发现方案需调整 → 回 planning 改 design 后重派。
     - **🛑 测试接缝 (seam) 门 (confirm 硬校验)** — 脚手架自带 `## 测试接缝 (seam)` 段, 三条规则: 优先复用现有接缝不新建 / 取最高接缝 (越靠外部行为越好) / 越少越好理想 1 个。**必须填实, 禁留占位** — `skein confirm` 跑 `validate_seam` 硬校验该段非占位 (旧 task 兼容态仅警告不拦), 与 `estimate-gate.md` 同级硬门。接缝质量 (选得对不对) 靠 grill 门与 `skein-spec analyze` 兜, confirm 只拦「没填」。
     - **当前方案 = 精简守现状 (YAGNI)** — design.md 正文只写满足当前需求的最小可行设计, 禁塞"以后可能要"的扩展点。
     - **可能性分支 section (研究期允许过度探索, 仅留痕)** — 现状之外的扩展方案 / 未来约束变化时的演进分支 / 被否决的备选, 写入「可能性分支」section, 每条**必须标触发条件**。不进最终设计方案正文, 不进 task.json DAG, 不生成 subtask。
     - **难逆决策实时记 ADR**: 跨子系统 / 破坏式重构 / 选型类 task, 难逆决策当场记进「取舍」/「可能性分支」段 (选了什么 · 否了什么 · 为什么), 防回退代价高的决策无痕迹蒸发。
   - **子任务 + 调度 DAG (协议先行, 后并行)** — 拆分铁律: 先把 subtask 间的**共享契约** (接口签名 / 数据结构 / 类型 / 协议格式 / DB schema) 抽成**单个前置 subtask** 优先定死, 下游各实现 subtask 只 `--deps` 这一个契约 subtask、彼此**不互挂依赖** → 契约一 done 即全批并行。每个 subtask 含 depends_on + 验收 checklist, 逐条 `skein subtask add <id> <sid> --name --desc [--deps --check --skills]` 落进 task.json。exec 一律派 `skein-executor`, 不再按 subtask 挑 agent。**这是 exec 唯一调度真值源**, 不写 mermaid 图文件。subtask 拆分 + 依赖登记模板详见 [dispatch-graph.md](dispatch-graph.md)。
     - **tracer-bullet (端到端瘦实现优先, ask-matt 同源)** — 契约 subtask 本身该是**端到端穿通的最瘦实现** (各层 stub / 空实现但全链路跑通一个 happy path): 第一个 subtask 完成后能验证「整条路走得通」, 再逐 subtask flesh 内部逻辑。早一个周期发现协议缺陷, 是压 makespan 的第二命门。
     - **拆完对表复杂度天花板 (硬)** — subtask 落完立刻对天花板表逐项核。
6. **异步派 skein-dedup (fire-and-forget, 不阻塞 exec)** — 所有 task planning 完成 (batch 末 / plan 收尾, exec 触发前), main **异步派 `skein-dedup`** subagent 全量扫一次未完成 task: ① 查重归并 (自动 `subtask add` 迁入主 task + `skein del` 次 task); ② 给散落的相关 task 补执行序织成完整 DAG (自动 `skein deps`, **仅对现无 deps 的 pending task 补前置, 已有 deps 的不碰**)。**异步不阻塞**: dedup 后台跑, exec 照常推进。
7. **出口 (按路由分流)** — 完成判据勾满后:
   - **flow (缺省 / 任务描述)** → `skein confirm` 转就绪, **直接续 exec 阶段**, 禁停手问用户要不要执行。
   - **显式 `plan`** → 停在 `skein start` 前, 提示用户 `/skein-flow exec <task>` 激活。

## 完成判据

- [ ] task 已 `create` (含可读 slug)
- [ ] prd.md 已填完 (六段 `- [ ] TODO: 填X` 占位**已全部整行替换**为真实内容; **目标/验收标准两章条目一律保持 `- [ ]` 未勾 — 勾选归 check 阶段**)
- [ ] subtask 已规划 (`subtask add` 落 task.json DAG)
- [ ] 设计方案已定 (design.md 正文含 `## 测试接缝 (seam)` 段已填实; 或 main 判定豁免)
- [ ] 预计工时已填 (`skein estimate <id> --set <小时数>`; `skein confirm` 硬校验非空正数, 规则详见 [estimate-gate.md](estimate-gate.md))

未勾满 = planning 未收敛, 禁 `skein start` / 禁转 exec。`skein confirm` 亦会逐项硬拒 (subtask/prd/预计工时任一缺失即报错阻断)。

## 失败模式

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| brainstorm 用户答不出关键分歧 | 给 2-3 推荐选项让用户选 (非开放式问) | 仍答不出 → 标「需求未定」, 停在 planning, 禁 start |
| grill 弱点表 >3 轮不收敛 | 归并同源弱点, 一次批量 `AskUserQuestion` 裁完 | 仍发散 → scope 过大, 拆多 task (heavy 档 + depends_on) |
| subtask 粒度不清 / 无从定 depends_on | 回 brainstorm 补边界, 按可独立验收切 | 仍切不动 → 派 `skein-researcher` 勘察代码再拆 |

## 延伸引用

- [dispatch-graph.md](dispatch-graph.md) — subtask 拆分 + 依赖登记模板
- [estimate-gate.md](estimate-gate.md) — 预计工时硬校验规则
