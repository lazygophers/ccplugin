# obra/superpowers 深度调研 — 对 skein skill/agent 写法的借鉴

> 数据源: 经 agent-reach (AVAILABLE) 探测后, 直接 `gh repo clone obra/superpowers` 浅克隆 (本调研 2026-07-18, release 2fa01ceb / plugin v6.1.1)。证据均为 `/tmp/superpowers/<file>:<line>`。skein 现状对照为 `/Users/luoxin/persons/lyxamour/ccplugin/plugins/tools/skein/<file>:<line>`。
> 罗盘: skein 是 task 编排框架 (main 调度器 + subagent 执行 + task.json 持久化 + worktree 隔离 + grill 硬门), superpowers 是方法论 skill 库 (brainstorm→plan→SDD→finish 的对话式工作流)。借鉴判定 = 以 skein 既有罗盘为准。

---

## 维度 1: 框架核心 — skills 怎么组织 / 如何组合

### superpowers 做法

- **14 个 skill 扁平命名空间** (`/tmp/superpowers/skills/` ls): brainstorming / writing-plans / subagent-driven-development / executing-plans / test-driven-development / systematic-debugging / verification-before-completion / requesting-code-review / receiving-code-review / using-git-worktrees / finishing-a-development-branch / dispatching-parallel-agents / writing-skills / using-superpowers。**无 agents/ 目录** (全程用通用 `general-purpose` subagent + skill 内嵌 prompt 模板驱动)。
- **组合靠 skill 间单向 handoff, 不是脚本编排**: brainstorming SKILL.md:61 终态 = "The terminal state is invoking writing-plans. Do NOT invoke any other skill."; writing-plans SKILL.md:168-174 Execution Handoff 二选一 (subagent-driven-development | executing-plans); SDD SKILL.md:406-413 Integration 段明确列出 required workflow skills。每个 skill 末尾 Integration 段固定指向下游 skill。
- **orchestration = 顺序约定, 无状态机**: 没有 task.json / claim / done 持久化层。靠 `using-superpowers` (SKILL.md:1-62) 在 SessionStart 注入, 强制"skill 适用必用", 由 LLM 自觉按 handoff 链推进。
- **核心 skill 写法 (brainstorming SKILL.md:1-159)**: frontmatter (name+description) → HARD-GATE 标签 → Anti-Pattern 段 → Checklist (create a task per item) → Process Flow (graphviz `dot` mermaid) → The Process 正文 → Key Principles → Visual Companion。结构高度模板化。

### skein 现状

- **10 skill + 7 agent 分层** (skills/ + agents/): skill 做流程编排 (flow/plan/grill/exec/check/finish), agent 做执行角色 (executor/researcher/checker/finisher/memorier/dedup/setup)。skill 间委托靠 skein-flow SKILL.md:16-26 显式 4 步闭环 (plan→exec→check→finish), 比 superpowers 的松散 handoff 更结构化。
- **组合靠 task.json DAG + 脚本编排**: subtask `depends_on` 落 task.json (scheduling-algorithm.md:5-9), `skein claim/done/fail` 脚本维护态。比 superpowers "靠 LLM 自觉" 更强 (持久化 + 跨 compaction 存活)。

### 罗盘判定: 演进 (已超越), 不照搬

skein 的 skill+agent 分层 + task.json DAG 编排, 在**持久化/并发/跨 compaction** 维度已超越 superpowers 的松散 handoff。superpowers 无 agent 概念, 全用 general-purpose + 内嵌 prompt 模板 — 这对 skein 的 Recursion Guard (工具层剔除 Agent/Task) 是倒退。**不照搬 superpowers 的组织方式**, 但可借鉴其 **skill 末尾 Integration 段** 的显式上下游声明写法 (见维度 5 具体建议)。

---

## 维度 2: skill 文件结构 — frontmatter / 正文 / references / 触发

### superpowers 做法

- **frontmatter 极简**: 只 `name` + `description` 两字段 (writing-skills SKILL.md:95-97), description **只写 when to use, 不写 what it does** (writing-skills SKILL.md:150-172 SDO 核心: "description 摘要 workflow 时 agent 会 follow description 跳过读 body")。≤1024 字符。
- **正文模板** (writing-skills SKILL.md:105-137): Overview (1-2 句 core principle) → When to Use (含 NOT to use) → Core Pattern (before/after) → Quick Reference → Implementation → Common Mistakes → Real-World Impact。
- **references 用法**: heavy reference (100+ 行) 才拆出独立文件, 否则 inline (<50 行 inline)。sdd SKILL.md 拆出 implementer-prompt.md + task-reviewer-prompt.md; systematic-debugging 拆出 root-cause-tracing.md / defense-in-depth.md / condition-based-waiting.md。**扁平, 一层深** (anthropic-best-practices.md:353-381 "Keep references one level deep")。
- **触发机制**: 全靠 description 匹配 (writing-skills SKILL.md:144-198), 无 `user-invocable` / `model` / `effort` 字段。命名 gerund (writing-plans / executing-plans / dispatching-parallel-agents)。

### skein 现状

- **frontmatter 重**: 含 `description` + `user-invocable` + `argument-hint` + `arguments` + `model` + `effort` (skein-plan SKILL.md:1-9, skein-exec SKILL.md:1-9)。description **既写 when 又写 what** (如 skein-exec description: "task 闭环入口 + exec 调度门...含双层调度算法 + 异步任务清单")。
- **references 用法一致**: skein-exec/references/{scheduling-algorithm.md, progress-reporting.md}, skein-plan/references/{breaking-refactor.md, dispatch-graph.md}, 一层深。与 superpowers 同构。

### 罗盘判定: 借鉴 (description 瘦身 + SDO 原则) — 高价值

**关键发现 (维度最高价值)**: superpowers writing-skills SKILL.md:150-172 明确验证 — **description 摘要 workflow 会让 agent follow description 跳过读 SKILL body**, 造成 "只做 1 轮 review 而非 2 轮" 的实例。skein-plan/grill/exec 的 description 都是大段 workflow 摘要, 正中此陷阱。

具体写法建议:
1. **description 瘦身**: 砍掉 workflow 摘要, 只留触发条件 + 症状。如 skein-plan description 可从当前 200+ 字降到 "planning 阶段入口。新建/并入 task 做需求梳理 + 方案设计时使用 (跨文件/多步任务必建 task), 产出 prd/design/findings + 子任务 DAG。无参=只规划不执行, --continue=不停返回工件"。删掉 "判新旧 + create 登记 + brainstorm + grill 硬门" 这类流程枚举 (那是 body 的事)。
2. **frontmatter 字段保留**: `user-invocable`/`model`/`effort`/`argument-hint` 是 skein 独有且服务于命令路由/成本分级, 比 superpowers 的纯 description 触发更可控, **不学 superpowers 极简 frontmatter**。
3. **正文模板**: skein 现状的 frontmatter→铁律→流程→失败模式→反例 结构已比 superpowers 更系统, 保持。可补 superpowers 的 Overview "1-2 句 core principle" 起首 (skein 多数 skill 直接进流程, 缺一句心法)。

---

## 维度 3: dispatch 模板 — 派 sub-agent 的 prompt 模板 (对比 skein 6 字段)

### superpowers 做法

- **dispatch 模板单独拆文件** (不在 SKILL.md 内): sdd SKILL.md:266-269 引用 implementer-prompt.md + task-reviewer-prompt.md + requesting-code-review/code-reviewer.md。模板用 ``` fenced code block 包裹, 是**填空模板** (placeholders 大写: `[BRIEF_FILE]` `[REPORT_FILE]` `[MODEL]` `[BASE_SHA]` `[HEAD_SHA]`)。
- **implementer-prompt.md (139 行) 结构**: Subagent 头 (description + model REQUIRED + prompt) → Task Description (Read task brief first) → Context (scene-setting) → Before You Begin (问问题) → Your Job (6 步) → Code Organization → When You're in Over Your Head (STOP/escalate) → Before Reporting Back: Self-Review (Completeness/Quality/Discipline/Testing) → After Review Findings → Report Format (写文件 + 回传 <15 行)。
- **task-reviewer-prompt.md (189 行)**: 双 verdict (spec compliance + code quality), Do Not Trust the Report (treat report as unverified claims), Tests (不重跑 implementer 已跑的), Calibration (severity 分级 Critical/Important/Minor, plan-mandated 标注)。
- **model 显式指定** (implementer-prompt.md:8-9, SDD SKILL.md:99-130): Mechanical→cheap model / Integration→standard / Architecture→most capable; "An omitted model inherits session's most expensive — silently defeats this section"。**Reviewers floor = mid-tier** (SDD SKILL.md:119-122, turn count beats token price)。
- **File Handoffs (SDD SKILL.md:219-264)**: 任务产物 (brief/report/diff) 一律落文件, dispatch prompt 只给路径, 不内联贴 — "Everything you paste stays resident in your context for the rest of the session"。`scripts/task-brief` / `scripts/review-package` 抽取。

### skein 现状

- **dispatch 6 字段自包含** (scheduling-algorithm.md:60-89): 目标/已知/工作目录与范围/输出格式/验收标准/失败处理, 内嵌 "执行纪律 (硬性)" 4 条 (Recursion Guard / 改前查上游 / 缺信息不硬猜 / spec 优先 / 写前硬门读后写)。模板内联在 references/scheduling-algorithm.md, 不拆独立文件。
- **无 model 分级**: skein subtask `--agent` 选 agent (默认 skein-executor), agent frontmatter 固定 model (executor 无 model 字段=继承, researcher=opus high), 不按任务复杂度动态选 model。

### 罗盘判定: 部分借鉴 (model 分级 + File Handoffs + Self-Review) — 中高价值

skein 的 6 字段比 superpowers 的 implementer-prompt 更紧凑且**显式含执行纪律** (Recursion Guard/读后写硬门), 这是 superpowers 没有的强项 (superpowers 靠通用 agent + prompt 文本)。但 skein 可借鉴:

1. **model 分级 (高价值)**: superpowers 的 Mechanical→cheap / Architecture→most capable 是硬成本杠杆, skein 全用同 model 浪费。建议 subtask 登记时 `--agent` 旁加 `--model` hint (或 agent 内部按 subtask `--check` 复杂度自选)。**需用户裁**: 是否引入 subtask 级 model 字段 (改动 task.json schema)。
2. **File Handoffs (中价值)**: skein 现状 dispatch 直接内联全部上下文, 大 subtask dispatch prompt 易超长。可学 superpowers 把 brief/产物落 `.skein/task/<id>/briefs/<sid>.md`, dispatch 只给路径。**但**: skein subtask 粒度小于 superpowers task, 多数场景 inline 够用, YAGNI 优先。
3. **Self-Review (中价值)**: superpowers implementer 回传前自带 Completeness/Quality/Discipline/Testing 自检, skein-executor.md:24 自查只说 "按验收标准逐条对照 + 跑局部命令", 可补 4 维自检 prompt (尤其 YAGNI/Did I only build what was requested — 契合 skein 反例编码)。
4. **dispatch 模板拆独立文件 (低价值, 可选)**: superpowers 把 implementer-prompt/reviewer-prompt 拆出来便于迭代, skein 内联在 scheduling-algorithm.md 也 OK (skein 调度算法和 dispatch 强耦合)。

---

## 维度 4: 失败模式 + 反例编码 — if-then 三段式 / 反模式黑名单

### superpowers 做法

- **失败模式编码靠 4 类机制叠加** (writing-skills SKILL.md:459-475 Match the Form to the Failure, **这是最有价值的发现**):
  - **Prohibition + rationalization table + red flags** → 用于 "知道规则但压力下违反" (discipline failure)
  - **Positive recipe / contract (what output IS)** → 用于 "合规但输出形状错" (shaping failure)
  - **Structural REQUIRED field/slot** → 用于 "漏了已产出物的某元素"
  - **Conditional on observable predicate** → 用于 "行为该依赖条件"
- **关键实证 (writing-skills SKILL.md:470)**: prohibition 在 shaping 问题上**适得其反** — "head-to-head wording tests on dispatch-prompt guidance, prohibition arm produced clearly more of the unwanted content than recipe arm (fully separated distributions), trended worse than no-guidance control"。
- **rationalization table + Red Flags** (TDD SKILL.md:256-288, systematic-debugging SKILL.md:215-244, verification SKILL.md:64-74): 每条 "Excuse | Reality" 二列; Red Flags = 内心独白黑名单 ("This is just a simple question" / "I'll just do this one thing first")。
- **Iron Law + "Violating letter = violating spirit"** (TDD SKILL.md:14, 31-45): 规则起首 "NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST", 紧跟 "Delete means delete / No exceptions"。
- **无 if-then 三段式表格**: superpowers 失败模式是散文 + table, 不是 skein 的 "触发→一线修复→仍失败兜底" 三列。

### skein 现状

- **if-then 三段式表格** (skein-flow SKILL.md:40-49, skein-plan SKILL.md:70-76, skein-exec SKILL.md:60-66, skein-check SKILL.md:39-45): 每个核心 skill 统一格式, 比 superpowers 更结构化。
- **反例段** (skein-flow SKILL.md:51-53, skein-plan SKILL.md:78-80, skein-exec SKILL.md:68-70): "违反上文即流程错误: ..." 一句话枚举。
- **grill 立场段** (skein-grill SKILL.md:17-22): "对抗非审批 / 找不到盲点≠通过" 近似 superpowers 的 "spirit over letter"。

### 罗盘判定: 借鉴 (Match the Form to the Failure + Iron Law + rationalization table) — 最高价值

**这是本调研对 skein 最有价值的发现**: superpowers writing-skills SKILL.md:459-475 的 **"Match the Form to the Failure"** 表格, 用实测数据证明了 **prohibition 在 shaping 问题上适得其反**。skein 现状大量用反例黑名单 (反例段), 但未区分 failure type。

具体写法建议:
1. **按 failure type 选编码形式 (高价值)**: skein 审视现有反例段, 对 "shaping failure" (如 dispatch prompt 太长 / 回传不压缩 / 进度清单 4 列不齐) 改用 **positive recipe** ("输出格式 IS: 4 列表 id/状态/摘要/进度%, 状态枚举进行中/等待中/阻塞") 而非 prohibition ("禁贴全量 diff")。对 "discipline failure" (跳 grill / inline 改源码 / 宣称派 agent 无 tool_use) 保持 prohibition + rationalization table。
2. **加 rationalization table (中价值)**: skein 现有反例是行为枚举, 缺 "agent 内心独白→reality" 对照。可给 grill/exec 补 Red Flags 表 (如 grill: "太顺没盲点" → "换角度深挖"; exec: "main 顺手改一行" → "硬门, 必派 subagent")。
3. **Iron Law 起首 (中价值)**: TDD/systematic-debugging/verification 三个 superpowers skill 都以 "Iron Law: NO X WITHOUT Y" 起首。skein-flow 的 "执行载体铁律" 已有此意, 可提炼成单行 Iron Law 置顶 (如 "NO SOURCE EDIT BY MAIN WITHOUT AGENT TOOL_USE")。
4. **保留 skein if-then 三段式**: 这是 skein 独有的强项 (superpowers 无), 不动。

---

## 维度 5: 检查点设计 — 硬门 / STOP 标记 (对比 skein grill 硬门)

### superpowers 做法

- **HARD-GATE 标签** (brainstorming SKILL.md:12-14): `<HARD-GATE>Do NOT invoke any implementation skill, write any code... until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.</HARD-GATE>`。
- **EXTREMELY-IMPORTANT / SUBAGENT-STOP 标签** (using-superpowers SKILL.md:6-16): `<SUBAGENT-STOP>` (subagent 忽略此 skill) + `<EXTREMELY-IMPORTANT>` (1% chance 适用就要用)。
- **checklist per item todo** (brainstorming SKILL.md:22, SDD SKILL.md 全程): "You MUST create a task for each of these items"。
- **Pre-Flight Plan Review (SDD SKILL.md:85-97)**: 开工前批量扫 plan conflict, 一次性问用户, 不逐个打断。
- **STOP 条件散落各 skill**: SDD SKILL.md:367-389 "Never:" 清单; systematic-debugging SKILL.md:215 "Red Flags - STOP"; verification SKILL.md:52 "Red Flags - STOP"。

### skein 现状

- **🛑 emoji + (硬门 · STOP) 文字** (skein-flow SKILL.md:19, skein-plan SKILL.md:53, skein-grill SKILL.md:33): 统一标记。
- **grill 硬门** (skein-grill SKILL.md:33-36): "planning 硬门 (强制 · STOP): start 前 MUST 跑一轮, 未跑 grill 禁 start"。比 superpowers HARD-GATE 更明确 (HARD-GATE 是 skill 内, grill 是跨 skill 闭环门)。
- **载体铁律** (skein-flow SKILL.md:12-13): "执行载体铁律 (最高优先级)" 11 条。

### 罗盘判定: 借鉴 (标签统一化 + checklist→todo 机制) — 中价值

skein 的 🛑 emoji + "(硬门 · STOP)" 已比 superpowers 散落的 STOP 更统一。可借鉴:

1. **固定标签词表 (中价值)**: superpowers 用 XML-like 标签 (`<HARD-GATE>` `<EXTREMELY-IMPORTANT>` `<SUBAGENT-STOP>`) 视觉锚点强。skein 可统一一套 (如 `🛑 硬门` / `⚠️ 硬规` / `❌ 反例`), 全 skill 一致, 便于 agent 识别。**需用户裁**: emoji vs 文字标签偏好。
2. **checklist→todo 强制 (中价值)**: superpowers brainstorming/SDD 明确 "create a task per checklist item"。skein 的 prd `- [ ] TODO` 章节已有此意但未强制 main 建 todo。可在 skein-plan 加 "checklist 每项 MUST 建 todo"。
3. **Pre-Flight 批量扫 (中价值)**: SDD Pre-Flight Plan Review (开工前一次批量问冲突, 不逐个打断) 与 skein grill 的 "归并同源弱点一次批量 AskUserQuestion" (skein-grill SKILL.md:44) 同源, skein 已有, 强化即可。
4. **保留 grill 跨 skill 硬门**: 比 superpowers HARD-GATE 更强, 不动。

---

## 维度 6: token 控制 — skill 体积 / 注入策略 (对比 skein hook 注入)

### superpowers 做法

- **SessionStart 注入唯一 skill** (hooks/session-start:1-45): 只注入 `using-superpowers/SKILL.md` 全文 (62 行), 包裹 `<EXTREMELY_IMPORTANT>`, 其余 13 个 skill 靠 `Skill` tool 按需加载。**只注入这一个**。
- **跨平台 hook 输出格式分支** (hooks/session-start:30-44): Cursor→`additional_context` / Claude Code→`hookSpecificOutput.additionalContext` / Copilot CLI→`additionalContext` (SDK standard)。一个 hook 适配多 harness。
- **token 效率硬指标** (writing-skills SKILL.md:214-266): getting-started <150 words / frequently-loaded <200 words / other <500 words; 技术: move details to `--help`, cross-reference (不 @ force-load), compress examples, eliminate redundancy。
- **无 @ force-load** (writing-skills SKILL.md:278-288): "@ syntax force-loads files immediately, consuming 200k+ context", 改用 `**REQUIRED SUB-SKILL:** Use superpowers:xxx`。

### skein 现状

- **SessionStart 注入**: (未直接读到 skein 的 session-start hook, 但 skein-researcher SKILL.md 提及 "SubagentStart 已注入的 core 全文即硬约束", scheduling-algorithm.md:72 "SubagentStart 已注入的 core" — 推测 skein 有 core 规则注入机制)。**需: 确认 skein SessionStart/SubagentStart hook 注入了什么、注入量。**
- **skill 体积**: skein-flow 53 行 / skein-plan 80 行 / skein-grill 59 行 / skein-exec 70 行 / skein-check 49 行 — 均精简, 大量内容拆 references。符合 superpowers <500 words 导向。
- **hook 注入对比**: (需确认 skein 具体策略)。

### 罗盘判定: 借鉴 (注入策略 + cross-reference 纪律) — 中价值 (待确认 skein hook 现状)

1. **只注入 bootstrap skill (中价值)**: superpowers 只注入 using-superpowers 一个, 其余按需 Skill tool 加载。skein 若 SessionStart 注入了大量 core 规则, 可审视是否瘦身到只注入"必用 skill 索引"。**需: 读 skein hook 源码确认注入内容。**
2. **跨平台 hook 格式分支 (低价值, 已不需要)**: skein 是 Claude Code 专用 plugin (非 superpowers 的 10+ harness), 无需多格式分支。
3. **cross-reference 纪律 (中价值)**: superpowers 明确禁 @ force-load (writing-skills SKILL.md:286)。skein references 用 `[xxx](references/xxx.md)` 相对链接 (非 @), 已合规, 保持。
4. **skill 体积**: skein 已达标, 不动。

---

## 维度 7: 独特机制 — superpowers 有但 skein 无的设计

### 7.1 Skill Discovery Optimization (SDO) — superpowers 独有, 高价值

writing-skills SKILL.md:140-276 整节, 核心: description 只写 when-to-use (见维度 2) + keyword coverage (错误信息/症状/同义词/工具名) + 动词命名。**skein 无 SDO 概念, description 偏 workflow 摘要**。借鉴: 见维度 2。

### 7.2 Micro-Test Wording Before Full Scenarios — superpowers 独有, 高价值

writing-skills SKILL.md:576-585: 写 skill 文案前, 5+ reps × 单次 fresh-context API call 微测, 含 no-guidance control, "variance is a metric" (5 个不同解释 = 文案不 binding)。**skein 无 skill 文案测试方法论** (CLAUDE.md 的 claude-p 质量门是单次测, 非 control + reps)。借鉴: skein skill 优化时可引入 micro-test (5 reps + control) 替代单次 claude-p。

### 7.3 skill = TDD for documentation (RED-GREEN-REFACTOR) — superpowers 独有, 高价值

writing-skills SKILL.md:8-18, 374-393: 写 skill 前先跑 pressure scenario 看 agent 不带 skill 怎么失败 (RED baseline), 再写 skill (GREEN), 再堵 loophole (REFACTOR)。Iron Law: "NO SKILL WITHOUT A FAILING TEST FIRST / Write skill before testing? Delete it"。**skein 的 skill-dev 方法论 (skills/skill-dev/) 需对照确认是否有 baseline 测试**。借鉴: skill 优化走 baseline→改→再测。

### 7.4 Model Selection per role — 见维度 3 (skein 无)

### 7.5 Durable Progress ledger — superpowers 独有, 部分已有

SDD SKILL.md:246-264: "Conversation memory does not survive compaction... Track progress in a ledger file"。skein 的 task.json subtasks[] + claim/done 脚本是更强的持久化 (跨 compaction + 并发安全), **已超越**, 不照搬。

### 7.6 File Handoffs (brief/report/diff 落文件) — 见维度 3

### 7.7 using-superpowers bootstrap (1% rule + Red Flags table) — 部分借鉴

using-superpowers SKILL.md:10-16 "1% chance applicable 就 MUST use" + SKILL.md:33-51 Red Flags table (12 条内心独白)。skein 无"skill 适用必用"的 bootstrap 注入 (依赖用户显式 /skein-flow 等命令触发)。**这是哲学分歧**: superpowers 是"自动触发方法论", skein 是"显式命令编排 task"。**不建议照搬 1% rule** — skein 的命令驱动 + 硬门更可控, 1% rule 会导致简单任务也被强推 task 闭环 (skein-flow 已有作用域边界豁免表 SKILL.md:30-36 抵御, 但 1% rule 会削弱它)。

### 7.8 two-stage review (spec compliance + code quality 双 verdict) — 中价值

SDD SKILL.md:8, task-reviewer-prompt.md:78-135: reviewer 一次读 diff 返回双 verdict (spec 合规 + 代码质量), Critical/Important/Minor 分级, plan-mandated 标注。skein-check 的 checker 验证 (lint/type/test/契约/一致性) 是多轴但单 verdict (PASS/FAIL + 冲突对)。借鉴: skein-checker 报告可引入 severity 分级 (Critical/Important/Minor) 而非二元 PASS/FAIL, 与 superpowers 对齐。**但**: skein-check 已有"回 planning 重确认方向"机制, severity 分级是锦上添花。

### 7.9 视觉 companion / graphviz 流程图 — 低价值, skein 不需要

brainstorming visual-companion.md (浏览器 mockup) + 全 skill 用 graphviz dot 流程图。skein 是命令行编排框架, 无视觉 mockup 需求; 流程图 skein 用文字 DAG (task.json) 而非 graphviz, 更适合脚本驱动。

---

## 总结: 按 skein 罗盘的优先级排序

| 优先级 | 借鉴项 | 来源 | 落点 | 理由 |
|---|---|---|---|---|
| **P0 最高** | Match the Form to the Failure (prohibition vs recipe 按失败类型选) | writing-skills:459-475 | skein 各 skill 反例段重审 | 实测证明 prohibition 在 shaping 问题上适得其反, skein 现有反例段未区分类型 |
| **P0 最高** | description 瘦身 (只写 when-to-use, 删 workflow 摘要) | writing-skills:150-172 | skein-plan/grill/exec description | 实测 description 摘要 workflow 会让 agent 跳过读 body |
| **P1 高** | Micro-Test (5 reps + no-guidance control) 替代单次 claude-p | writing-skills:576-585 | skill-dev 方法论 / CLAUDE.md 质量门 | skein 现有 claude-p 质量门是单次测, 缺 control + variance |
| **P1 高** | rationalization table + Red Flags (内心独白→reality) | TDD:256-288 / using-superpowers:33-51 | skein-flow/exec/grill 补充 | skein 反例是行为枚举, 缺内心独白对照 |
| **P1 高** | model 分级 (Mechanical→cheap / Architecture→capable) | SDD:99-130 | subtask 级 model hint (需改 task.json) | 硬成本杠杆, skein 全同 model 浪费 |
| **P2 中** | Iron Law 单行置顶 (NO X WITHOUT Y) | TDD:31 / verification:18 | skein-flow "执行载体铁律" 提炼 | 视觉锚点, 规则优先级显式 |
| **P2 中** | implementer Self-Review 4 维 (Completeness/Quality/Discipline/Testing) | implementer-prompt:80-105 | skein-executor.md:24 自查段 | 补 YAGNI 自检, 契合 skein 反例 |
| **P2 中** | 标签词表统一 (🛑硬门 / ⚠️硬规 / ❌反例) | using-superpowers XML 标签 | 全 skill 统一 | 视觉锚点一致性 |
| **P2 中** | two-stage review severity 分级 (Critical/Important/Minor) | task-reviewer-prompt:124-137 | skein-checker 报告格式 | 比二元 PASS/FAIL 更可操作 |
| **P3 低** | SessionStart 只注入 bootstrap skill | hooks/session-start | 待确认 skein hook 现状 | 需先读 skein hook |
| **P3 低** | checklist 每项强制建 todo | brainstorming:22 | skein-plan prd 章节 | 锦上添花 |
| **不照搬** | using-superpowers 1% rule (skill 适用必用) | using-superpowers:10-16 | — | 与 skein 命令驱动 + 作用域豁免哲学冲突 |
| **不照搬** | 无 agent 概念 (全 general-purpose) | skills/ 无 agents/ | — | skein Recursion Guard 靠 agent 工具面, 倒退 |
| **已超越** | Durable ledger (task.json + claim/done) | vs SDD:246-264 | — | skein 持久化 + 并发安全更强 |
| **已超越** | 跨 skill 硬门 (grill) | vs HARD-GATE | — | skein grill 更明确 |
| **已超越** | if-then 三段式表格 | superpowers 无 | — | skein 独有强项 |

---

## 需要 (待 main/用户裁)

1. **skein SessionStart/SubagentStart hook 注入了什么**: 本调研未读 skein hooks 源码, 维度 6 注入策略建议依赖此确认。建议补查 `plugins/tools/skein/hooks/` 或 `.claude-plugin/`。
2. **subtask 级 model 字段是否引入**: 维度 3 / 7.4 的 model 分级需改 task.json schema + `skein subtask add --model`, 属设计决策, 需用户拍板。
3. **skill-dev 方法论现状**: 维度 7.2/7.3 的 Micro-Test / baseline TDD 建议需对照 skein `skills/skill-dev/` 确认是否已有 (本调研未读 skill-dev)。
4. **标签词表偏好**: 维度 5 的 emoji vs 文字标签, 需用户裁 (CLAUDE.md 已有 🛑 先例)。

