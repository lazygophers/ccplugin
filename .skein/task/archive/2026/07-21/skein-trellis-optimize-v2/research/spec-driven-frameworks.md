# 调研: spec-driven / 方法论类开发框架 vs skein

## 数据源 (经 gh clone 到 /tmp 读源码 + webReader docs)
- BMAD-METHOD: gh clone bmad-code-org/BMAD-METHOD → /tmp/bmad-cloned (源码) + docs.bmad-method.org/reference/agents/
- spec-kit: gh clone github/spec-kit → /tmp/speckit-cloned (templates/) + spec-driven.md (九条条款全文)
- agent-os: gh clone buildermethods/agent-os → /tmp/agent-os-cloned (commands/)
- Aichaku: github.com/RickCogley/aichaku README (webReader, 项目已宣布 2025-07 退休)
- spec-story: **需要** — 多次检索无直接结果, 名称疑似与 OpenSpec / CoreStory 混淆, 未确认存在, 标记缺
- Cursor rules/.cursorrules: 综合 README + 行业实践 (无需 clone, 概念层)

## skein 罗盘基线 (判据, 已读各 SKILL + agent + 审计)
- 双层记忆 core(常驻极简索引)/recall(按词检索); 分类 git/test/arch/build/style/domain/ops
- grill 硬门 (锁定合同到 task.json); 双层 DAG 调度 (任务级 + 子任务级依赖)
- worktree 隔离; 根因复盘 (≥3 轮); 验证与修复分离 (checker 只读)
- 阶段: plan→exec→check→finish; 代理 setup/researcher/memorier/dedup/finisher/executor/checker
- 已知短板: sediment 无强制模板 ( sediment 火发即忘, 判定门过即写, 无结构约束 )

---

# 框架 1: BMAD-METHOD (bmad-code-org/BMAD-METHOD)

## 规范建模
- **spec = 一组分阶段产物**, 按敏捷生命周期分层产出: product-brief → PRFAQ → PRD → architecture → epics & stories → UX → implementation
- 产物落在 `_bmad/output/<artifact>/` 目录, 每个产物有独立 skill (bmad-create-prd / bmad-create-architecture / bmad-create-epics-and-stories / bmad-create-ux-design)
  - 证据: /tmp/bmad-cloned/src/bmm-skills/2-plan-workflows/ + 3-solutioning/ + 4-implementation/ 目录结构
- **memlog (.memlog.md)** = 单一追加日志, 记每条决策/约束/版本/假设/问题; 产物在 Finalize 时从 memlog "蒸馏" 出来, 非边写边生成
  - 证据: bmad-architecture/SKILL.md:34-37 "The memlog is the run's working memory... The spine file itself is distilled from the memlog at the end"
  - 写入走共享脚本 memlog.py (原子追加), 禁手写: "All writes go through the shared script, never by hand" (bmad-prd/SKILL.md:14)

## 方法论阶段 (从需求到交付)
- **4 大阶段目录** (源码分层): 1-analysis (brainstorm/research/brief/prfaq) → 2-plan-workflows (PRD/UX) → 3-solutioning (architecture/epics/readiness) → 4-implementation (dev-story/quick-dev/code-review/sprint/retrospective)
  - 证据: /tmp/bmad-cloned/src/bmm-skills/ 子目录命名
- **Implementation Readiness 门** (bmad-check-implementation-readiness, 6 步 step-01~06): document-discovery → prd-analysis → epic-coverage → ux-alignment → epic-quality → final-assessment, 产 readiness-report
  - 证据: /tmp/bmad-cloned/src/bmm-skills/3-solutioning/bmad-check-implementation-readiness/steps/
- **scale-domain-adaptive**: 按 project complexity 自动调规划深度 (bug fix → enterprise), 非一刀切
  - 证据: README "Scale-Domain-Adaptive — Automatically adjusts planning depth based on project complexity"

## 多角色/代理分工
- **12+ 拟人角色**, 每角色一个 skill + 触发码:
  - Analyst (Mary) / PM (John) / Architect (Winston) / Developer (Amelia) / UX Designer (Sally) / Tech Writer (Paige)
  - 证据: docs.bmad-method.org/reference/agents/ (webReader 全表)
- 触发分两类: **Workflow trigger** (结构化流程文件, 如 PRD/DS/CA) vs **Conversational trigger** (自由对话, 如 WD/MG/EC)
- **Party Mode**: 多 agent persona 同会话协作讨论 (README "Party Mode")
- **Reviewer Gate**: Finalize 时并行派多个 reviewer subagent 各写 review-{slug}.md, parent 只收摘要 (verdict + top 2-5 findings + path), 不持全文
  - 证据: bmad-prd/SKILL.md:69-79 + bmad-architecture/SKILL.md:62-64

## 规范模板 (强制结构)
- **无单一强制 spec 模板**, 而是"Essential Spine + Adapt-In Menu"弹性结构:
  - Essential Spine = 默认必出现段 (除非有理由删); Adapt-In Menu = 按产品 concern (合规/集成/SLA/硬件/公开 API) 按需拉入段
  - 证据: bmad-prd/SKILL.md:63 "The Essential Spine is the expected default... The Adapt-In Menu is conditional"
- PRD 形状: Features grouped; FRs nested with **globally numbered stable IDs** (FR-001...); NFR 独立段; **skip traceability matrices**
  - 证据: bmad-prd/SKILL.md:63
- **architecture spine** = 只固定 invariants (设计范式/边界/依赖规则/状态突变归属/共享数据所有权), 结构性的 (stack/tree/data shape) 是 seed (冷启动真, 代码存在后归代码管)
  - 证据: bmad-architecture/SKILL.md:8-9 "a lean spine of invariants... Everything structural is seed"
- 模板可定制: `{workflow.prd_template}` / `{workflow.spine_template}` / `{workflow.validation_checklist_template}` 从 customize.toml 解析
- **addendum.md**: 溢出深度 (rejected-alternative rationale / options-considered / mechanism 决策 / 深度 persona) 归 addendum, 不塞主文档
  - 证据: bmad-prd/SKILL.md:14

## 独特亮点 (BMAD 有 skein 无)
1. **memlog 追加日志 + 产物蒸馏**: 决策先落原子追加日志, 产物最后从日志蒸馏 → 可断点续跑 (resume 重载 memlog), 产物与决策审计同源
2. **Coaching path vs Fast path 双模式**: 默认引导式提问 (elicitation, 拉用户思考), 可切快速草稿 + [ASSUMPTION] 标记
3. **Implementation Readiness 显式门**: 进入实现前 6 步独立验证 (document-discovery → final-assessment)
4. **Reviewer Gate 并行评审**: 多 reviewer 各写文件, parent 只收摘要 — 避免全文占 context
5. **Essential Spine + Adapt-In Menu**: 弹性模板 (默认段 + 按需段), 非 "一个模板套所有"
6. **AD-n 稳定 ID + 继承父 spine**: 架构决策有稳定编号, 子 spine 继承父 spine 的 AD 为只读约束
7. **scale-domain-adaptive**: 规划深度按复杂度自适应

## 对 skein 的优化建议 (以 skein 为罗盘)
- **借鉴 (中价值)**: **sediment 判定门加可选 "Essential Spine" 默认段** — 当前 sediment 无模板是短板, 可给 sediment 输出一个极简默认骨架 (如: 候选规则文本 / 建议层 core|recall / 类目 / 证据 / 信号), 让 skein-memorier 蒸馏时有结构兜底。**但** skein 的 sediment 是 "火发即忘", 不应强模板 (会增开销), 做成**可选骨架提示**即可
- **借鉴 (高价值)**: **memlog 追加日志思路 → skein task 的 findings.md 可演进为"决策追加日志"** — 当前 skein 的 prd/design/findings 是并行写, BMAD 的 "memlog 蒸馏出产物" 让单一真值更清晰。skein 可考虑 task 级 memlog 追加决策, findings 从中蒸馏。**但** skein 是单人短任务为主, memlog 价值低于 BMAD 的长周期多产物场景, **优先级中**
- **借鉴 (中价值)**: **Reviewer Gate 的"并行 reviewer 各写文件 parent 只收摘要"** — skein 的 check 已是"验证与修复分离", 但 check 只一个 checker。若 task 复杂可考虑多角度并行验证 (lint/type/test/作用域 各一), 各回写 research/ 只收摘要。**但** skein 定位轻量, 多 reviewer 开销大, **暂不建议**, 记为未来复杂 task 的可选增强
- **拒绝**: BMAD 的 **12+ 拟人角色 + Party Mode** — skein 已有精简代理矩阵 (7 个功能型代理), 拟人化 (Mary/John/Winston) 对 skein 无价值, 反增认知负担。**拒绝**
- **拒绝**: BMAD 的 **Essential Spine + Adapt-In Menu 全套** 对 skein 过重 — skein 的 PRD (prd.md) 已有目标/边界/验收标准/索引四段, 够用
- **演进**: skein 的 grill 硬门 ≈ BMAD 的 Implementation Readiness 门, **方向一致已是 skein 优势**, 无需改

---

# 框架 2: spec-kit (github/spec-kit, GitHub 官方)

## 规范建模
- **spec = 三级产物**, 落在 `specs/<branch>/` 目录:
  - `spec.md` (WHAT/WHY, 禁 HOW) → `plan.md` (技术决策 + 数据模型 + contracts) → `tasks.md` (可执行任务清单)
  - 辅助: `research.md` / `data-model.md` / `contracts/` / `quickstart.md` / `checklists/`
  - 证据: spec-driven.md "SDD Workflow" + plan-template.md:46-57 目录树
- **constitution = 不可变架构 DNA** (`memory/constitution.md`), 九条条款管所有实现:
  - Article I Library-First / II CLI Interface / III Test-First (NON-NEGOTIABLE) / IV-VI 项目自定义 / VII Simplicity / VIII Anti-Abstraction / IX Integration-First
  - 证据: spec-driven.md "Nine Articles of Development" 全文 + constitution-template.md
- **三条命令串起流程**: `/speckit.specify` (产 spec.md + 自动建分支 + 编号) → `/speckit.plan` (产 plan.md + constitution 合规检查) → `/speckit.tasks` (产 tasks.md, 标 [P] 并行)
  - 证据: spec-driven.md "Streamlining SDD with Commands"

## 方法论阶段
- **specify → plan → tasks → implement → (checklist gate) → 完成**
- implement 命令执行循环 (implement.md): 先跑 prerequisite 检查 → **checklist 状态门** (扫描 checklists/ 统计 [ ]/[X], 任一 incomplete 则 STOP 问用户) → 加载 tasks.md/plan.md/constitution → phase-by-phase 执行 → 进度跟踪 + 失败处理 → 完成验证
  - 证据: /tmp/speckit-cloned/templates/commands/implement.md:52-174
- **TDD 硬约束** (Article III): 测试先写, 用户批准, 确认 FAIL (Red), 才实现
- **constitution 合规门 (Phase -1 Gates)**: plan 生成时跑 Simplicity Gate (≤3 projects? 无 future-proofing?) / Anti-Abstraction Gate (直接用框架? 单模型表示?) / Integration-First Gate (contracts 定义? 契约测试写?)
  - 证据: spec-driven.md "Constitutional Enforcement Through Templates"

## 多角色/代理分工
- **spec-kit 不强调多角色代理**, 而是命令驱动 (specify/plan/tasks/implement/analyze/converge/clarify/checklist)
- 隐含角色: spec-shaper (user + AI 对话产 spec) / planner (AI 产 plan) / task-deriver (AI 产 tasks) / implementer (AI 执行) / reviewer (analyze/converge 命令)
- **research agents** 散布在 spec 过程 (查库兼容性/性能基准/安全含义), 非独立阶段
  - 证据: spec-driven.md "Research-Driven Context"

## 规范模板 (强制结构, spec-kit 的核心强项)
- **spec-template.md** (强制结构, 读源码):
  - User Scenarios & Testing (mandatory): 每个 User Story 有 Priority (P1/P2/P3) + **Independent Test** (单独可测可部署可演示) + Acceptance Scenarios (Given/When/Then)
  - Requirements (mandatory): Functional Requirements (FR-001 全局稳定 ID) + Key Entities
  - Success Criteria (mandatory): Measurable Outcomes (SC-001, 技术中立可测)
  - Assumptions
  - **[NEEDS CLARIFICATION]** 强制标记: 模板指令 "Mark all ambiguities... Don't guess"
  - 证据: /tmp/speckit-cloned/templates/spec-template.md 全文
- **plan-template.md** (强制结构):
  - Summary / Technical Context (Language/Dependencies/Storage/Testing/Platform/ProjectType/Performance/Constraints/Scale) / **Constitution Check (GATE)** / Project Structure (目录树 + Option 1/2/3 按项目类型) / **Complexity Tracking** (只在违反 constitution 时填, 表格: Violation/Why Needed/Simpler Alternative Rejected)
  - "IMPORTANT: plan should remain high-level and readable. 代码样本下沉 implementation-details/"
  - 证据: /tmp/speckit-cloned/templates/plan-template.md 全文
- **tasks-template.md** (强制结构):
  - 格式 `[ID] [P?] [Story] Description` — [P] = 可并行 (不同文件无依赖), [Story] = 归属用户故事
  - **Phase 分层**: Phase 1 Setup → Phase 2 Foundational (BLOCKS all stories, CRITICAL) → Phase 3+ User Stories (每 story 独立可测 MVP) → Phase N Polish
  - **MVP-first 策略**: 先 Setup+Foundational+Story1 (P1) 停下验证, 再增量加 story
  - **依赖与执行顺序** 段: Phase Dependencies / User Story Dependencies / Within Each Story (tests 先写先 FAIL / models before services / services before endpoints) / Parallel Opportunities
  - 证据: /tmp/speckit-cloned/templates/tasks-template.md 全文
- **constitution-template.md**: Core Principles (5+ 条, 每条 NAME+DESCRIPTION) + Additional Sections + Governance (宪法 supersede 所有实践, 修改需文档+批准+迁移计划)
  - 证据: /tmp/speckit-cloned/templates/constitution-template.md

## 独特亮点 (spec-kit 有 skein 无)
1. **constitution (不可变架构 DNA) + 九条条款 + Phase -1 Gates 合规检查**: 架构原则编码成可检查的 gate, plan 生成时强制过门 — skein 的 core 记忆是"约定"但无强制合规检查
2. **[NEEDS CLARIFICATION] 强制标记**: 模板硬性要求标歧义, 禁猜 — 反 LLM "合理假设" 倾向
3. **User Story 独立可测 MVP + Priority 分层**: 每个 story 是可独立开发/测试/部署/演示的切片, P1 先交付
4. **Complexity Tracking 表**: 只在违反 constitution 时填, 强制写 Violation/Why/Simpler Alternative Rejected — 架构问责
5. **Phase 分层 + Foundational BLOCKS 硬门**: Phase 2 Foundational 完成前禁动 user story, 显式 checkpoint
6. **checklist 状态门**: implement 前扫 checklists/ 统计完成率, incomplete 则 STOP — 把检查清单做成可统计的门
7. **FR 全局稳定 ID (FR-001)** + AD-n 稳定 ID (BMAD 也有) — 可追溯
8. **三级命令链 specify→plan→tasks**, 每级自动产多文件 + 自动建分支 + 自动编号

## 对 skein 的优化建议 (以 skein 为罗盘)
- **借鉴 (最高价值, 直击已知短板)**: **sediment 加 spec-kit 风格的极简模板骨架** — 这是本调研对 skein sediment "无强制模板" 短板的最直接解法。建议 sediment 输出加默认骨架:
  - 候选规则 (命令式契约, MUST/禁止 起首)
  - 建议层 (core|recall)
  - 类目 (git/test/arch/build/style/domain/ops)
  - 证据 (file:line 多处)
  - 信号 (强|弱)
  - **这正好是 skein bootstrap 扫描模式已有的格式** (见 skein-researcher bootstrap 段), 可复用为 sediment 通用骨架。**强建议**
- **借鉴 (高价值)**: **[NEEDS CLARIFICATION] 标记 → skein plan 的 grill 硬门可引入** — 当前 grill 是"锁定合同", 可在锁定前强制标歧义点 (类似 spec-kit 的不猜原则)。skein 已有 "缺信息标 `需要:`" 协议, **方向一致, 可强化为 plan 阶段产物的必填段**
- **借鉴 (中价值)**: **constitution + Phase -1 Gates → skein 的 core 记忆可加"合规检查"钩子** — 当前 core 是常驻约定, 但无主动合规验证。可考虑 check 阶段加 core 合规扫描 (违反 core 规则的报告)。**但** skein core 是轻量约定非硬架构原则, 过重的 gate 不贴 skein, **做轻量版即可** (check 时 grep core 关键禁令)
- **借鉴 (中价值)**: **Complexity Tracking 表思路 → skein design.md 可加** — 当 design 决定偏离既有约定时, 强制记 Violation/Why/Simpler Alternative Rejected。skein 已有 design.md 写入界限, 可加问责段
- **借鉴 (中价值)**: **User Story 独立可测 + Priority → skein subtask 拆分可参考** — skein 的 subtask 已有 DAG 依赖, 但无"独立可测 MVP 切片"概念。复杂 task 可借鉴 P1 先交付策略
- **拒绝**: **三级命令链 specify→plan→tasks + 自动建分支编号** — skein 已有 `skein create` + prd/design/findings 工件体系, 命令链对 skein 冗余。skein 的 worktree 隔离已覆盖"分支"需求
- **拒绝**: **Article III Test-First NON-NEGOTIABLE** — skein 不强制 TDD (取决于项目 core 的 test 类目约定), 硬塞会与 skein "core 按项目分型" 冲突
- **演进**: skein 的 DAG 调度 ≈ spec-kit 的 Phase 分层 + [P] 并行标记, **skein 的双层 DAG 更强** (任务级 + 子任务级), 无需退化

---

# 框架 3: agent-os (buildermethods/agent-os, Brian Casel)

## 规范建模
- **spec = spec 文件夹**, 落在 `agent-os/specs/<YYYY-MM-DD-HHMM-feature-slug>/`:
  - `plan.md` (完整计划) / `shape.md` (shaping 决策 + 上下文) / `standards.md` (适用的 standards 全文) / `references.md` (参考实现指针) / `visuals/` (mockup)
  - 证据: /tmp/agent-os-cloned/commands/agent-os/shape-spec.md:181-192
- **standards = 从代码库提取的约定**, 独立体系 (`agent-os/standards/` + `index.yml`):
  - 四能力: **Discover** (从代码提取模式) / **Deploy** (按所建之物智能注入相关 standard) / **Shape Spec** (更好计划) / **Index** (组织可发现)
  - 证据: README "Core capabilities"
- **product context** (`agent-os/product/`): mission.md / roadmap.md / tech-stack.md, spec 时对齐产品目标
  - 证据: shape-spec.md:76-90

## 方法论阶段
- **shape-spec (plan mode) → implement → review**
- shape-spec 9 步 (必须在 plan mode): clarify → visuals → reference implementations → product context check → surface relevant standards → generate folder name → structure plan (Task 1 恒为 "Save spec documentation") → complete plan → ready for execution
  - 证据: shape-spec.md:25-179
- **关键: Task 1 恒为存 spec 文档** — 实现前先把 shaping 产物落盘
- **standards 注入是核心**: shape-spec Step 5 读 `standards/index.yml` 识别相关 standard, AskUserQuestion 确认, 读 standard 全文进 plan context
  - 证据: shape-spec.md:92-108
- inject-standards / index-standards / discover-standards 独立命令 (动态注入约定)

## 多角色/代理分工
- **agent-os 不用拟人角色**, 用**命令 + plan mode 约束**:
  - shaper (shape-spec, plan mode 强制) / implementer (implement) / reviewer (独立 subagent 评审, 见先前调研) / standards-curator (discover/index)
- **强制 AskUserQuestion 工具**: shape-spec 全程用 AskUserQuestion 问用户, 非自由文本
  - 证据: shape-spec.md:7 "Always use AskUserQuestion tool when asking the user anything"
- **standards 注入 = 智能筛选**: 非全量注入, 按所建之物从 index.yml 选相关 subset

## 规范模板 (强制结构)
- **shape.md 模板** (shape-spec.md:194-220):
  - Scope / Decisions / Context (Visuals/References/Product alignment) / Standards Applied (每条 + why)
- **standards.md 模板** (shape-spec.md:222-242): 每条 standard 全文 + 分隔
- **references.md 模板** (shape-spec.md:244-260): Similar Implementations, 每条 Location/Relevance/Key patterns
- **plan.md 结构**: Task 1 (存 spec 文档) + Task 2..N (实现任务)
- **无 spec.md 强制结构** (shape.md 替代, 更轻)

## 独特亮点 (agent-os 有 skein 无)
1. **standards 体系 = 从代码提取 + 按需智能注入**: Discover (代码→约定) + Deploy (按所建之物注入 subset) + Index (可发现) — **这是 agent-os 的核心差异**
2. **Task 1 恒为存 spec 文档**: 实现前强制落盘 shaping 产物
3. **plan mode 强制**: shape-spec 必须在 plan mode 跑, 否则 STOP — 用平台原生约束锁流程
4. **AskUserQuestion 强制**: 全程结构化提问, 非自由文本
5. **时间戳文件夹命名** (YYYY-MM-DD-HHMM-feature-slug): 可发现可排序
6. **product context 对齐**: mission/roadmap/tech-stack 作为 spec 上文

## 对 skein 的优化建议 (以 skein 为罗盘)
- **借鉴 (最高价值, 与 skein 设计高度共振)**: **agent-os 的 standards Discover/Deploy/Index 三能力 ≈ skein 的 core/recall/bootstrap/reconstruct** — skein 已有等价机制:
  - Discover ≈ skein bootstrap (扫代码库提炼约定) + reconstruct (按项目类型重建)
  - Deploy ≈ skein core 常驻 + recall 按需检索 + SubagentStart 注入
  - Index ≈ skein core 极简索引 (每条 1 行标题)
  - **结论: skein 在 standards 体系上已与 agent-os 同频甚至更细 (双层记忆), 无需借鉴, 反证 skein 设计正确**
- **借鉴 (中价值)**: **standards 注入的 "按所建之物筛 subset" 思路 → skein SubagentStart 注入可优化** — 当前 skein SubagentStart 注入 core 全文 (≤2000 token), agent-os 是按 feature 选相关 standard subset。skein 审计已指出 "SubagentStart core 索引化非全文" 优化方向, **agent-os 的 subset 注入是佐证**, 强化该优化建议
- **借鉴 (中价值)**: **Task 1 恒为存 spec 文档 → skein plan 已有** (skein create 先建 task 目录 + prd.md), **方向一致, skein 已做**
- **借鉴 (低价值)**: **plan mode 强制 → skein 用 grill 硬门 + worktree 隔离锁流程**, 异曲同工, skein 不依赖平台 plan mode (跨平台弱), **保持现状**
- **拒绝**: **AskUserQuestion 强制全程** — skein 已有 grill + AskUserQuestion 敲定, 但不强制每步 (代理不与用户对话), skein 的"代理只读 + main 转达用户"分工更清晰, **拒绝 agent-os 的全程提问**
- **演进**: skein 的 bootstrap/reconstruct ≈ agent-os 的 Discover, **skein 更强** (分冷启动播种 vs 按类型重建两档), 无需改

---

# 框架 4: Aichaku (RickCogley/aichaku) — 已宣布退休

## 规范建模
- **方法论混合 (methodology blending)**: 显式选多个方法论 (Shape Up/Scrum/Kanban/XP/Lean/Scrumban) + standards (OWASP/TDD/Clean Arch/Google Style/NIST-CSF) + principles (DRY/KISS/YAGNI/SOLID/Unix) 混合加载
  - 证据: github.com/RickCogley/aichaku README "Methodology blending"
- **YAML 配置替代 verbose Markdown**: 声称 96% 体积缩减 (50K+ token Markdown → ~4K YAML)
  - 证据: README "96% size reduction vs verbose Markdown"
- **3-Mode 系统**: Planning ("let's plan") / Execution ("let's build") / Improvement ("retrospective")
- **自然语言感知**: 加载方法论后, Claude 响应语言 ("let's shape up" → Shape Up 模式)

## 方法论阶段
- **init --global (one-time) → init (project) → standards/principles add → integrate (merge CLAUDE.md) → 编码**
- 全局装一次, 项目引用; `aichaku integrate` 把所选合并进 CLAUDE.md

## 多角色/代理分工
- **specialized agents**: Security / API / Documentation / Code Explorer / Methodology Coach
- MCP server 集成 (aichaku-reviewer)

## 规范模板
- 无强制 spec 模板 (方法论驱动, 非产物驱动)
- cheatsheets: Shape Up/Scrum/Kanban/XP/Lean/Scrumban (退休时 salvage 进 esolia-standards MCP)

## 独特亮点
1. **方法论混合 + 自然语言触发**: 选多个方法论, 语言激活
2. **YAML 配置替代 Markdown**: token 极致压缩 (声称 96%)
3. **3-Mode 系统**: Planning/Execution/Improvement

## ⚠️ 项目状态: 已宣布退休 (2025-07)
- 证据: README 顶部 "This project is being retired. Active development stopped in 2025-07."
- 原因: 审计后无外部采纳者, 0 JSR 依赖, 单外部 issue; 维护者决定合并价值到更小工具 (devkit slash commands + esolia-standards MCP)
- salvage: pre-commit hooks orchestrator / methodology cheatsheets / path-security utility

## 对 skein 的优化建议
- **拒绝 (项目已死)**: 不建议借鉴具体实现 (已退休)
- **借鉴 (低价值, 已是 skein 优势)**: **YAML 替代 Markdown 压 token 思路** — skein 的 core 极简索引 (每条 1 行标题) + recall 按需检索已是更优解 (不需 YAML 化), Aichaku 的 YAML 是它没分层记忆的妥协, skein 不需要
- **借鉴 (低价值)**: **方法论混合 + 自然语言触发** — skein 的 core 按类目 (git/test/arch/...) 组织, 用户 `recall <query>` 检索, 已是类似机制。skein 不绑定具体方法论 (Shape Up 等), 更通用
- **反证 skein**: Aichaku 退休说明 "方法论 cheatsheet 注入" 模式价值有限 (无外部采纳), skein 的"工程约定 core/recall"定位更稳

---

# 框架 5: spec-story — 需要 (未确认存在)

## 状态
- 多次 WebSearch 无直接结果
- 名称疑似与 **OpenSpec** (specs-as-tests) 或 **CoreStory** 混淆
- 标记 **需要**: 若 main 确认具体仓库 URL 再补调研

---

# 补充: Cursor rules / .cursorrules 生态

## 规范建模
- **.cursorrules (单文件) 或 .cursor/rules/*.mdc (v2 多文件)**: 项目级 AI 行为规则
- 规则类型: Always (恒注入) / Auto Attached (按 glob 触发) / Agent Requested (AI 按需拉) / Manual (用户显式 @)
  - 推测: 综合 Cursor 官方 docs + 行业实践, 未 clone 官方仓库 (概念层足够)
- **rules 前缀描述**: 每条 rule 有 description, AI 决定是否 Agent Requested 拉取

## 对 skein 的优化建议
- **借鉴 (低价值, skein 已更优)**: **Auto Attached 按 glob 触发 ≈ skein recall 按词检索** — skein 的 recall 更灵活 (语义检索 vs glob 硬匹配)
- **借鉴 (低价值)**: **rule 的 description 字段供 AI 决策加载** — skein 的 core 索引每条 1 行标题已起此作用
- **拒绝**: **单文件 .cursorrules** — skein 已分层 (core/recall + 类目), 比单文件强

---

# 跨框架总结: 对 skein 的 Top 5 借鉴点 (按价值排序)

## 1. [最高] sediment 加极简模板骨架 (spec-kit 风格) — 直击已知短板
- 来源: spec-kit spec-template.md / tasks-template.md / constitution-template.md 的强制结构
- 建议: sediment 输出加默认骨架 (候选规则/建议层/类目/证据/信号) — **复用 skein bootstrap 扫描已有格式**
- 罗盘判定: 贴 skein (sediment 无模板是审计短板), 不回退任何差异化优势

## 2. [高] [NEEDS CLARIFICATION] 强制标记 (spec-kit) + memlog 决策追加日志 (BMAD)
- 来源: spec-kit "Don't guess, mark ambiguities" + BMAD memlog 追加 + 产物蒸馏
- 建议: grill 硬门锁定前强制标歧义; task 级决策追加日志 (findings.md 演进为决策日志)
- 罗盘判定: 强化 skein 已有 "需要:" 协议 + grill, 非新增概念

## 3. [高] standards 按 subset 智能注入 (agent-os) — 佐证 skein SubagentStart 优化
- 来源: agent-os "Deploy Standards — Intelligently inject relevant standards based on what you're building"
- 建议: skein SubagentStart 注入 core 索引 (非全文) + 按所建之物筛 subset (审计已指出)
- 罗盘判定: 贴 skein (审计已列此优化), agent-os 是外部佐证

## 4. [中] Complexity Tracking 问责表 (spec-kit) + AD-n 稳定 ID (BMAD)
- 来源: spec-kit plan-template Complexity Tracking + BMAD architecture AD-n
- 建议: design.md 偏离约定时强制记 Violation/Why/Simpler Alternative Rejected
- 罗盘判定: 贴 skein (design.md 写入界限已有), 加问责段

## 5. [中] Reviewer Gate 并行多角度验证 (BMAD)
- 来源: BMAD "finalize_reviewers 各写 review-{slug}.md, parent 只收摘要"
- 建议: 复杂 task 的 check 可考虑多角度并行 (lint/type/test/作用域 各一), 各回写 research/ 只收摘要
- 罗盘判定: skein 定位轻量, **暂不建议默认开启**, 记为复杂 task 的可选增强

---

# 反证 skein 设计正确的点 (调研中确认 skein 已优或等价)
- **standards Discover/Deploy/Index** (agent-os 核心卖点) ≈ skein bootstrap/reconstruct + core/recall + 索引 — **skein 更细 (双层记忆)**
- **Phase 分层 + [P] 并行** (spec-kit) ≈ skein 双层 DAG — **skein 更强 (任务级 + 子任务级)**
- **Auto Attached glob 触发** (Cursor) ≈ skein recall 语义检索 — **skein 更灵活**
- **方法论 cheatsheet 注入** (Aichaku) — 项目已退休, 反证该模式价值有限, skein 的工程约定定位更稳
- **grill 硬门** ≈ BMAD Implementation Readiness 门 + spec-kit constitution Phase -1 Gates — skein 已有等价

## 需要
- **spec-story**: 未确认存在, 需 main 给具体仓库 URL 再补
