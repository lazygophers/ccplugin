# Matt Skills 全量覆盖审计

审计对象: Matt Pocock 全部 22 正式 skills (engineering 17 + productivity 5) SKILL.md 本体方法论 vs skein 现状 (skein-plan / skein-exec / skein-check / skein-finish / skein-flow / skein-grill / skein-research / skein-spec / skein-clean / skein-setup + 各 references)。

判定档: **深** (方法论要点全覆盖) / **中** (有对应缺部分要点) / **弱** (仅概念提及无方法论) / **空白** (无对应) / **超范围** (非工程任务不覆盖)。

## 总览

- 深: 9 个 (ask-matt, grill-with-docs, implement, code-review, tdd, to-spec, to-tickets, setup-matt-pocock-skills, grilling)
- 中: 7 个 (diagnosing-bugs, codebase-design, domain-modeling, triage, improve-codebase-architecture, research, writing-great-skills)
- 弱: 2 个 (wayfinder, prototype)
- 空白: 2 个 (resolving-merge-conflicts, handoff [判定为已被工件层替代, 非真空白, 详见单项])
- 超范围: 2 个 (teach, grill-me [grill-me 概念已融入 brainstorm, 但 standalone stateless 形态超范围])

净需补齐 (弱 + 真空白): **3 个** (wayfinder / prototype / resolving-merge-conflicts)。

---

## 逐 skill 判定

### engineering

#### ask-matt
- 深度: **深**
- skein 对应: skein-flow「🧭 场景路由」表 (skein-flow/SKILL.md:50-64) + matt-pocock-mapping.md 全表
- 差距: 无。ask-matt 本体是路由器 (描述 flow / on-ramps / standalone / vocabulary 分层), skein-flow 场景路由表 7 行覆盖全部场景信号, mapping.md 22 条逐 skill 对照完整。路由理念 (该走 flow 直接走 / 简单直接做 / 灰区才问用户) 已由 skein-flow「作用域边界」(skein-flow/SKILL.md:36-48) 内建。
- 补齐: 无需

#### code-review
- 深度: **深**
- skein 对应: skein-check (skein-check/SKILL.md:25-37 验证 / 契约逐条 / 一致性核查)
- 差距: 极小。matt 两轴 (Standards + Spec) → skein 翻译为「lint/type/test/build + 契约合规 + 一致性核查」, Standards 轴对应 lint/type/build + 既有 spec 规则, Spec 轴对应 prd 验收标准 + 契约逐条验证。matt 的 Fowler 12 code smells (Mysterious Name / Duplicated Code / Feature Envy / ...) 清单 skein 未显式列举, 但 skein-checker 跑 lint + 一致性冲突检测 (重复实现同一职责 / 命名与约定相斥) 覆盖了其中可机械化检测的子集。
- 补齐: 无需硬补。若要强化 Standards 轴, 可选把 12 smells 清单作为 skein-checker 的可选参考清单 (软建议, 非缺口)

#### codebase-design
- 深度: **中**
- skein 对应: skein-plan/references/design-vocabulary.md (词表 7 词: module/interface/depth/seam/adapter/leverage/locality)
- 差距 (matt 有 skein 缺):
  - **deletion test** (删掉模块复杂度是否消失) — matt codebase-design.md:62-64 明确列为原则, skein design-vocabulary.md 未提
  - **"interface is the test surface"** 原则 — matt codebase-design.md:64 未在 skein 词表
  - **"one adapter = hypothetical seam, two = real"** 原则 — matt codebase-design.md:65 未在 skein 词表
  - **deepening cluster 给定依赖** (DEEPENING.md) + **design-it-twice 并行子 agent 设计多接口** (DESIGN-IT-TWICE.md) — matt 两个外部 ref, skein 无对应方法论
  - **deep vs shallow 图示 + "设计接口三问"** (减方法 / 简化参数 / 藏复杂度) — skein 只一句"倾向 deep module"
  - **为可测性设计三原则** (accept deps / return results / small surface) — matt codebase-design.md:68-95, skein 无
- 补齐 (s2, 进 design-vocabulary.md): 补「原则」段 — deletion test + interface-is-test-surface + 1-vs-2-adapter 原则 + 为可测性设计三原则。design-it-twice 并行设计可作为「可能性分支」section 的操作指引 (单一文件, 不新增 skill)

#### diagnosing-bugs
- 深度: **深**
- skein 对应: skein-exec「🔴 tight feedback loop」(skein-exec/SKILL.md:48) + skein-check/references/root-cause-protocol.md (5 维根因)
- 差距: 无实质。matt diagnosing-bugs 6 阶段 (build feedback loop → reproduce+minimise → hypothesise 3-5 → instrument → fix+regression → cleanup+post-mortem) → skein 翻译: Phase 1 tight loop = skein-exec「先复现」硬门 (dispatch prompt MUST 含「先复现」); Phase 3-4 hypothesise/instrument = root-cause-protocol 5 维探针 (需求/方案/实现/环境/测试); Phase 6 post-mortem hand-off to improve-codebase-architecture = root-cause-protocol「同类防」+ sediment 沉淀。
  - 次要点未直译: matt Phase 3「hypothesis 3-5 ranked + 示用户」显式数量, skein 未硬性要求 ≥3 假设; matt「tag debug log [DEBUG-xxx] 前缀」收尾 grep 清理 — skein 无此纪律
- 补齐: 无需硬补。若强化可在 root-cause-protocol 补「假设 ≥3 ranked」「debug log 打前缀」两条软纪律 (可选)

#### domain-modeling
- 深度: **中**
- skein 对应: skein-plan brainstorm (词汇澄清) + design-vocabulary.md ADR 机制 + skein-grill「drift 一致性」/「scope 吸收」轴
- 差距 (matt 有 skein 缺):
  - **CONTEXT.md 专属 glossary 文件** — matt 主动维护 `CONTEXT.md` 作纯术语表 (禁实现细节), skein 用 prd/design 工件 + spec recall 替代, 无独立 glossary 单一真值源
  - **多 context (CONTEXT-MAP.md) 布局** — matt 支持单/多 context (monorepo), skein 无对应概念
  - **ADR 三触发条件** (hard-to-reverse + surprising + real-trade-off 三者全中才记) — matt domain-modeling.md:66-73 明确门槛, skein design-vocabulary.md ADR 段只说「难逆决策」未列三条件
  - **challenge-against-glossary / sharpen-fuzzy / discuss-concrete-scenarios / cross-reference-with-code 四主动动作** — skein brainstorm 有词汇澄清但未列这四类主动挑战动作
- 补齐 (s2, 分两处):
  - design-vocabulary.md ADR 段补「三触发条件门槛」(避免 ADR 滥用)
  - 是否引入独立 CONTEXT.md glossary 文件 — **架构决策, 归 main+用户**: skein 现有 prd/design + spec recall 已能承术语, 强行加 CONTEXT.md 会与现有工件重叠 (YAGNI 反面)。建议不补, 仅在 design-vocabulary.md 注明「术语落在 prd 词汇段 / spec recall, 不另建 CONTEXT.md」

#### grill-with-docs
- 深度: **深**
- skein 对应: skein-grill + skein-plan brainstorm (prd.md/design.md 持久化)
- 差距: 无。grill-with-docs 本体仅一行「Run /grilling session using /domain-modeling」, 实质是 grilling primitive + stateful 文档落地。skein-grill (7 审查轴 + relentless interview 提问法) + brainstorm + prd/design 工件落地完整覆盖。
- 补齐: 无需

#### implement
- 深度: **深**
- skein 对应: skein-exec (skein-exec/SKILL.md 调度门 + 自愈闭环)
- 差距: 无。matt implement 本体 5 行 (use /tdd at pre-agreed seams / typecheck regularly / single test files regularly / full suite at end / code-review / commit), skein-exec 全覆盖: tdd → subtask 验收标准约束 + tight feedback loop; 定期 typecheck/single test/full suite → dispatch prompt 执行纪律 + skein-check 跑 lint/type/test/build; code-review → skein-check; commit → skein-finish (commit→merge→archive)。
- 补齐: 无需

#### improve-codebase-architecture
- 深度: **中**
- skein 对应: matt-pocock-mapping.md:34「skein 独立 task 改进类走标准四步闭环」
- 差距 (matt 有 skein 缺):
  - **Explore 阶段 YAGNI scope-before-scan** — matt 先查 commit 历史 hotspot 再扫 (improve-codebase-architecture.md:20-23), skein 仅说「独立 task」未给扫描方法论
  - **HTML 可视化报告 + before/after 图示 + Tailwind/Mermaid CDN** — matt 产出 `<tmpdir>/architecture-review-<ts>.html` 含每候选 card (Files/Problem/Solution/Benefits/Before-After 图/推荐强度 badge), skein 无对应可视化产物
  - **deletion test 扫描摩擦点** — 同 codebase-design 差距
  - **grilling loop 选定候选后** — 选定候选跑 grilling, 副作用 inline 更新 CONTEXT.md/ADR, skein 走 plan brainstorm + design 可覆盖但无「候选选择 → grill 深化」的显式两段
- 补齐 (s2, 进 matt-pocock-mapping.md 该行 + 可选新 reference): 若用户真要做架构改进, 补「扫描方法论 (commit hotspot + deletion test + 摩擦点清单)」作为该场景的操作指引。HTML 可视化报告 — **架构决策归 main+用户**: skein 哲学是工件落 `.skein/` markdown (非 HTML 临时文件), 强行加 HTML 报告偏离 skein 工件范式。建议不补 HTML, 改进类 task 走 design.md「架构」+「可能性分支」承载候选

#### prototype
- 深度: **弱**
- skein 对应: skein-flow/SKILL.md:61「独立 sandbox task 原型验证 (不落主仓库)」+ matt-pocock-mapping.md:55「skein-researcher 只读勘察 或 独立 sandbox task」
- 差距 (matt 有 skein 缺, 较大):
  - **throwaway-from-day-one 纪律 + 标记** — matt prototype 明确「throwaway code that answers a question」, 命名让读者看出是 prototype, skein 无 throwaway 纪律
  - **两分支路由** — LOGIC (状态模型 terminal app) vs UI (多变体 URL search param + 浮动底栏), skein 无分支路由
  - **六规则** (throwaway 标记 / one command to run / no persistence / skip polish / surface state / capture when done) — skein 无
  - **capture-when-done** (验证后 fold 进真代码 + 把 prototype 作 primary source commit 到 throwaway 分支 + 留 context pointer) — skein 无对应「原型 → 结论回流主 task」机制
- 补齐 (s2): 若要真覆盖, 需在 skein-plan 或新 reference 加「prototype 纪律」: throwaway 标记 + 两分支 + 六规则 + capture-when-done 回流。但 **skein 主仓库零改动范式** (一切落 task worktree) 与 matt「prototype 紧邻使用处」冲突 — 实操上 skein 用户走「独立 sandbox task + worktree」即可, throwaway 由 worktree 销毁天然保证。建议: 在 matt-pocock-mapping.md:55 该行扩写「sandbox task 纪律 (throwaway 命名 + one command + no persistence + 验证后 fold 结论回主 task design.md)」, 不新增 skill

#### research
- 深度: **深**
- skein 对应: skein-research + skein-researcher agent + findings.md 收敛机制
- 差距: 无实质。matt research 3 点 (primary sources / cited md / 存 repo 既有约定处) → skein-research 数据源分层 (代码勘察 + agent-reach 优先外部检索) + researcher 结论落 `.skein/task/<id>/research/<slug>.md` + findings.md 收敛 (skein-plan:84「researcher 回传后 main 写 findings.md」)。skein 比 matt 更细 (分层 + agent-reach 探测门 + 失败模式三段式)。
- 补齐: 无需

#### resolving-merge-conflicts
- 深度: **空白**
- skein 对应: skein-finish/SKILL.md:43 失败模式「`skein finish` merge 冲突 → 读冲突文件手动解 → 重跑 finish → 解不开停手报用户」仅一行兜底
- 差距 (matt 有 skein 缺, 完整方法论):
  - matt 5 步: ① see current state (git history + conflicting files) ② find primary sources (commit messages / PRs / issues 理解每方 intent) ③ resolve each hunk (preserve both intents / incompatible 则按 merge 目标选 + note trade-off / 禁 invent new behavior / always resolve never --abort) ④ discover + run automated checks (typecheck → tests → format) ⑤ finish merge/rebase (stage + commit / rebase continue 到所有 commit rebased)
  - skein 仅「读冲突文件手动解」, 无「读 primary sources 理解 intent」「preserve both intents」「never --abort」「run checks」「rebase continue」纪律
- 补齐 (s2, 必补): merge 冲突在 skein-finish merge 阶段 + 多 task 并行 worktree 合并时真实发生。建议在 skein-finish/references 新增 `merge-conflict-resolution.md` (或扩 skein-finish 失败模式行), 落 matt 5 步纪律。**这是本次审计最明确的真空白**

#### setup-matt-pocock-skills
- 深度: **深**
- skein 对应: skein-setup (skein-setup/SKILL.md 5.9K) + `skein init`
- 差距: 无实质。matt setup 配 issue tracker / triage labels / domain doc layout (探索 → 呈现 → 确认 → 写), skein-setup + `skein init` 配 `.skein/config.yaml` + 工件布局。skein 用自身 `.skein/` 布局替代 matt 的 `docs/agents/*.md` + `CONTEXT.md` 布局, 理念同 (per-repo 配置一次性)。
- 补齐: 无需

#### tdd
- 深度: **深**
- skein 对应: matt-pocock-mapping.md:19「skein-exec subtask 内部 TDD 实践 (skein 不强制 TDD, 由 subtask 验收标准约束)」+ skein-exec tight feedback loop + skein-check 验收逐条
- 差距 (matt 有 skein 缺, 但 skein 已显式选择不强制):
  - **pre-agreed seams** — matt tdd 明确「Test only at pre-agreed seams. 写测试前写下 seams 并与用户确认, 未确认 seam 不写测试」, skein subtask 验收标准隐含 seam 但无「pre-agree seam」显式纪律
  - **anti-patterns 三类** — implementation-coupled (mock internals / test private / side channel) + tautological (assertion 重算 expected 同代码逻辑) + horizontal-slicing (全测试先写再全实现), skein 无反模式清单
  - **red-before-green + one-slice-at-a-time + refactor-not-in-loop 三规则** — skein 无显式 TDD loop 规则
- 评估: skein **设计上选择不强制 TDD** (mapping.md:19 明示), 这是架构决策非缺口 — skein 用「subtask 验收标准 + tight feedback loop + check 跑 test」替代强制 red-green loop。但 anti-patterns 三类 + pre-agreed seam 是方法论增量, 即使不强制 TDD 也可作为 subtask 验收标准编写指引补强
- 补齐 (s2, 可选软补): 若要强化测试质量, 在 dispatch-graph.md 或 design-vocabulary.md 补「测试反模式三类 + pre-agreed seam」作为 subtask 验收标准编写参考。**不改变 skein 不强制 TDD 的架构决策**。若 main 判定保持现状, 标「无需」

#### to-spec
- 深度: **深**
- skein 对应: skein-plan 产出 prd.md + design.md (skein-plan:95-97 prd 章节目标/边界/验收/索引 + design.md 架构/取舍/选型)
- 差距: 无实质。matt to-spec template (Problem Statement / Solution / User Stories / Implementation Decisions / Testing Decisions / Out of Scope / Further Notes) → skein prd (目标/边界/验收/索引) + design (架构/数据流/取舍/选型/可能性分支)。matt「seams at highest point + 理想 seam 数 = 1」→ skein-plan 契约 subtask 单前置 (skein-plan:102「定协议是唯一真串行」)。
  - 次要点: matt User Stories 极长编号清单格式 skein 未硬性要求; matt「Do NOT include specific file paths or code snippets」纪律 skein 有同理 (design.md 写方案不写路径)
- 补齐: 无需

#### to-tickets
- 深度: **深**
- skein 对应: skein-plan `subtask add --deps` (skein-plan:102 subtask DAG + depends_on) + tracer-bullet (skein-plan:103) + breaking-refactor.md (expand-contract + strangler fig)
- 差距: 无实质。matt to-tickets tracer-bullet (vertical slice 穿各层 / 单 context window 大小 / blocking edges) → skein subtask DAG + depends_on + tracer-bullet 端到端瘦实现。matt wide refactor 的 expand-contract 序列 → skein breaking-refactor.md 全覆盖 (expand 加新形式 → migrate batches → contract 删旧 + strangler fig 变体 + integration branch 兜底)。
- 补齐: 无需

#### triage
- 深度: **中**
- skein 对应: matt-pocock-mapping.md:26「skein-plan 登记前查未完成 task (查重归并) + skein-dedup 异步织 DAG」
- 差距 (matt 有 skein 缺):
  - **状态机** — matt triage 5 状态角色 (needs-triage / needs-info / ready-for-agent / ready-for-human / wontfix) + 2 类别 (bug/enhancement) + 状态转移规则, skein 无 issue 状态机 (skein task 状态机是 pending/进行中/检查中/已完成, 非 triage 角色)
  - **redundancy check + prior rejection (.out-of-scope/)** — matt triage 主动查代码已有实现 + 读 .out-of-scope/ KB 防重复拒, skein-dedup 查重但无 .out-of-scope/ KB
  - **verify claim (复现 bug / 跑 PR diff)** — matt triage step 3 验证声明真实性, skein 无对应 (skein 假设用户输入已成型需求)
  - **AGENT-BRIEF.md / OUT-OF-SCOPE.md 产物** — matt 产 agent-ready brief + out-of-scope KB, skein 无对应产物
- 评估: triage 是「处理外部涌入的未成型 issue」, skein 设计假设是「用户直接给需求进 plan」, 两者场景不完全重叠。skein-dedup 的查重归并覆盖了 triage 的 dedup 维度, 但「外部 issue 状态机 + agent brief 产物」是 skein 未覆盖的独立场景
- 补齐 (s2, 架构决策归 main+用户): 若 skein 要支持外部 issue 涌入 (如 GitHub issue → skein task), 需新增 triage 状态机 + agent-brief 产物机制。若 skein 定位保持「用户直接驱动」, 则 triage 超范围不补。建议: 在 matt-pocock-mapping.md:26 该行注明「skein 覆盖 dedup 维度, 完整 issue 状态机 + agent-brief 超 skein 当前定位, 需外部 triage skill 增强」, 维持现状

#### wayfinder
- 深度: **弱**
- skein 对应: matt-pocock-mapping.md:28「skein-plan research 判定门 + 复杂度天花板 + supertask」
- 差距 (matt 有 skein 缺, 大):
  - **decision-ticket map 机制** — matt 核心: 巨大模糊努力 → issue tracker 上 chart「shared map」(label `wayfinder:map`) + child decision tickets (label `wayfinder:<research|prototype|grilling|task>`), 每票解一个 decision 非交付物, 推 fog of war 直到路清晰。skein supertask→task→subtask 三层是「交付物拆分」非「decision 拆分」, 理念不同
  - **fog of war + Not yet specified + Out of scope 三段** — matt map 结构 (Destination / Notes / Decisions so far / Not yet specified / Out of scope), skein 无对应 map 工件
  - **HITL vs AFK ticket 类型** — matt 每票标 HITL/AFK + 4 类型 (research/prototype/grilling/task), skein subtask 无类型标记
  - **claim by assignee + native blocking** — matt ticket assignee 即 claim, skein 用 subtask claim 但无「map 级共享 map 工件」
  - **plan-don't-do 哲学** — matt wayfinder 默认产 decisions 非 deliverables, 手-off 到 to-spec 时机明确; skein 复杂度天花板拆多 task 后各 task 直接进 plan-exec, 无「先决策后建造」两段
- 评估: wayfinder 是 matt 最 cognitively demanding 的 flow, 处理「跨多 session 看不清全貌的巨大努力」。skein 现有 supertask + research 判定门 + 复杂度天花板覆盖了「拆多 task + 调研」维度, 但「decision-ticket map 推雾」这一核心理念 skein 无对应。skein 倾向直接进 plan-exec (即使 heavy 档也是强化 grill 后拆 task), 而非先建 map 解决策再 collapse 到 spec
- 补齐 (s2, 架构决策归 main+用户): **这是本次审计最大的理念差距**。是否引入 decision-ticket map 机制是 skein 定位决策 — 若 skein 要支持「跨数周/数 session 的巨大模糊努力」, 需新增 wayfinder-like map 工件 + decision ticket 类型。若 skein 定位「单 session 到数天的 task 编排」, 则 supertask 已够, wayfinder 超范围。建议: 不补原生实现, 在 matt-pocock-mapping.md:28 该行扩写「skein supertask 覆盖交付物拆分维度, decision-ticket map 推雾机制超 skein 当前定位, 需外部 wayfinder skill 增强」, 并在 skein-plan 复杂度天花板处加一句「若需求跨多 session 看不清全貌, 建议先用外部 wayfinder 建 decision map, 再 collapse 进 skein plan」

### productivity

#### grill-me
- 深度: **超范围** (概念已融入, standalone stateless 形态超 skein 定位)
- skein 对应: skein-plan brainstorm + skein-grill 提问法 (relentless interview 内置)
- 差距: grill-me 是「无 codebase 的 stateless interview, 不存本地不建 CONTEXT.md」, skein brainstorm 总是落在 `.skein/` task 工件 (stateful)。但 skein-grill 提问法 (一次一问 / 带推荐答案 / 事实自查决策交用户 / 共识才放行) 完整复刻 grilling/grill-me primitive
- 补齐: 无需。skein 设计上总是 stateful (task 工件), stateless interview 形态超范围。若用户要纯访谈无 task, 可直接对话无需 skill

#### grilling
- 深度: **深**
- skein 对应: skein-grill (skein-grill/SKILL.md:23-29 提问法 + review-axes-and-output.md 7 审查轴)
- 差距: 无。grilling primitive (relentless interview / walk decision tree / one question at a time / fact自查 decision交用户 / 共识才放行) → skein-grill 提问法 1:1 复刻 + 叠加 skein 专属层 (7 审查轴 + planning 硬门 + 弱点表 + task.json 契约锁定)。skein-grill:24 明示「优先用 /grill-me 引擎, 未装则用内置提问法兜底」。
- 补齐: 无需

#### handoff
- 深度: **空白 → 实为已被工件层替代 (非真缺口)**
- skein 对应: matt-pocock-mapping.md:47「已由 skein task.json + prd/design/findings 工件 + sediment spec 完整替代, 不单列」+ skein-plan:33 smart zone 接近上限时「压进 prd.md/design.md 工件 (工件即跨 context 持久态)」
- 差距: matt handoff 压缩对话成 md 文件 + suggested skills 段 + redact 敏感信息 + 新 session 引用承上下文 (fork)。skein 用 task 工件 (prd/design/findings/task.json) + sediment spec 作跨 context 持久层, 设计上消解了 handoff 需求 — 每个 subtask / 新 session 从 task 工件 reload 即恢复上下文, 无需手动压缩对话
- 评估: 这是 skein 的**架构优势而非缺口**。matt 无 task 持久层故需 handoff, skein 有 task 持久层故 handoff 内生于工件。matt-pocock-mapping.md:47 判定正确
- 补齐: 无需。已在 mapping.md 显式标注「完整替代不单列」

#### teach
- 深度: **超范围**
- skein 对应: 无 (matt-pocock-mapping.md:57 显式标注「skein 不覆盖, 非工程任务超范围」)
- 差距: teach 是多 session 教学 (MISSION.md / reference/*.html / learning-records / lessons/*.html / assets 组件库 / zone of proximal development / fluency vs storage strength / desirable difficulty), 纯学习场景非工程任务编排
- 补齐: 无需。超 skein (任务编排) 定位

#### writing-great-skills
- 深度: **中**
- skein 对应: matt-pocock-mapping.md:58「本仓库 skills/skill-dev/ (skein 同仓的 skill 开发方法论)」
- 差距 (需核 skills/skill-dev/ 实际内容, 本次未深读):
  - matt writing-great-skills 核心方法论: predictability 是根德 / model-invoked vs user-invoked (context load vs cognitive load 取舍) / 信息分层 (in-skill step / in-skill reference / external reference + progressive disclosure + context pointer) / 何时 split (by invocation / by sequence) / pruning (single source of truth + no-op test 逐句) / leading words / 6 failure modes (premature completion / duplication / sediment / sprawl / no-op / negation)
  - skein 同仓 `skills/skill-dev/` 是否覆盖上述全部要点未核实 (本次审计范围是 skein skills vs matt, skills/skill-dev 是另一目录)
- 补齐: 需 s2 或后续审计 Read skills/skill-dev/ 核实。若 skills/skill-dev/ 已覆盖 predictability / 信息分层 / split / pruning / leading words / failure modes 则深, 否则补。本次标「中」基于未核实

---

## 需补齐清单 (按优先级, 供 s2 执行)

### P0 (真空白, 必补)

1. **resolving-merge-conflicts** → `skein-finish/references/merge-conflict-resolution.md` (新增) 或扩 skein-finish/SKILL.md:43 失败模式行
   - 补: matt 5 步纪律 (see state / find primary sources 理解 intent / resolve each hunk preserve both intents never --abort 禁 invent / run typecheck→tests→format checks / finish merge + rebase continue 到所有 commit)
   - 理由: merge 冲突在 skein-finish merge 阶段 + 多 task worktree 合并时真实发生, 当前仅一行兜底

### P1 (弱, 建议补)

2. **wayfinder** → `skein-flow/references/matt-pocock-mapping.md:28` 该行扩写 + `skein-plan/SKILL.md` 复杂度天花板段加一句
   - 补: 注明「skein supertask 覆盖交付物拆分维度, decision-ticket map 推雾机制超 skein 当前定位」, 在复杂度天花板处加「跨多 session 看不清全貌的巨大努力建议先用外部 wayfinder 建 decision map 再 collapse 进 skein plan」
   - 理由: 巨大模糊努力的 decision-map 机制是 skein 最大理念差距, 但补原生实现是定位决策, 先标注边界 + 引导外部 skill

3. **prototype** → `skein-flow/references/matt-pocock-mapping.md:55` 该行扩写
   - 补: sandbox task 纪律 (throwaway 命名让读者看出是 prototype / one command to run / no persistence by default / skip polish / surface state / 验证后 fold 结论回主 task design.md + prototype 作 primary source commit 到 throwaway 分支留 context pointer)
   - 理由: 当前仅「独立 sandbox task」一句, 无 throwaway 纪律 + capture-when-done 回流机制

### P2 (中, 方法论增量, 可选软补)

4. **codebase-design** → `skein-plan/references/design-vocabulary.md` 「原则」段
   - 补: deletion test + interface-is-test-surface + 1-vs-2-adapter 原则 + 为可测性设计三原则 (accept deps / return results / small surface) + 设计接口三问
   - 理由: 当前词表只有定义无原则, matt 原则层缺失

5. **domain-modeling** → `skein-plan/references/design-vocabulary.md` ADR 段
   - 补: ADR 三触发条件门槛 (hard-to-reverse + surprising + real-trade-off 三者全中才记, 防滥用)
   - 不补: 独立 CONTEXT.md glossary (与 prd/design + spec recall 重叠, YAGNI)

6. **tdd** → `skein-plan/references/dispatch-graph.md` 或 design-vocabulary.md
   - 补 (可选): 测试反模式三类 (implementation-coupled / tautological / horizontal-slicing) + pre-agreed seam 纪律, 作为 subtask 验收标准编写参考
   - 不改: skein 不强制 TDD 的架构决策维持

7. **improve-codebase-architecture** → `skein-flow/references/matt-pocock-mapping.md:34` 该行扩写
   - 补: 扫描方法论 (commit 历史 hotspot + deletion test + 摩擦点清单 5 问) 作为改进类 task 的 plan 阶段操作指引
   - 不补: HTML 可视化报告 (偏离 skein markdown 工件范式)

8. **triage** → `skein-flow/references/matt-pocock-mapping.md:26` 该行扩写
   - 补: 注明「skein-dedup 覆盖 dedup 维度, 完整 issue 状态机 + agent-brief 超 skein 当前定位, 需外部 triage skill 增强」
   - 不补原生: triage 状态机超 skein「用户直接驱动」定位

### 待核实 (非本次审计范围)

9. **writing-great-skills** → 需 Read `skills/skill-dev/` 核实是否覆盖 matt 方法论 (predictability / 信息分层 / split / pruning / leading words / 6 failure modes)。本次标「中」基于未核实, s2 或后续审计深读 skills/skill-dev/ 定夺

---

## 架构决策项 (归 main + 用户裁定, 非自动补)

以下差距补不补取决于 skein 定位决策, s2 不应自作主张:

- **wayfinder 原生实现**: 是否引入 decision-ticket map 机制支持跨数 session 巨大模糊努力? (当前建议: 不补原生, 标注边界引导外部 skill)
- **triage 原生实现**: 是否支持外部 issue 涌入 (GitHub issue → skein task)? (当前建议: 不补, 超定位)
- **CONTEXT.md glossary**: 是否引入独立术语表文件? (当前建议: 不补, prd/design + spec recall 已覆盖, YAGNI)
- **HTML 可视化报告**: 改进类 task 是否产 HTML? (当前建议: 不补, 偏离 skein markdown 工件范式)

main 判定后告知 s2 补哪些。
