# 调研: mindfold-ai/Trellis 设计细节 vs skein 借鉴原料

## 数据源 (经 agent-reach 探测 = AVAILABLE, 实际用 gh clone 到 /tmp 读源码 + webReader docs)
- clone: gh repo clone mindfold-ai/Trellis (main 分支, depth 1)
- docs: docs.trytrellis.app
- 源码: packages/cli/src/{configurators,migrations,templates}, .claude/hooks/*.py, .cursor/skills/*, .trellis/{workflow.md,config.yaml,spec/}

## Trellis 整体模型 (5 层)

| 层 | 路径 | 职责 |
|---|---|---|
| workflow | .trellis/workflow.md | 三阶段 (Plan/Execute/Finish) + `[workflow-state:STATUS]` tag block 真值源 |
| persistence | .trellis/{tasks,spec,workspace} | 任务/规范/会话日志 |
| platform integration | .{claude,cursor,codex,opencode,...}/ | 17 平台适配 (hooks/settings/agents/skills/commands) |
| channel runtime (v0.6) | ~/.trellis/channels/ + .trellis/agents/ | 多 agent 协作 (event log/forum/thread) |
| mem (v0.6) | ~/.{claude,codex,pi}/sessions/ | 跨会话对话检索 (读本地 JSONL) |

---

## 维度 1: spec 注入机制 (implement.jsonl / check.jsonl)

### Trellis 做法
- 格式 (`.trellis/tasks/<task>/implement.jsonl`): 每行一个 JSON `{"file":"<repo-relative path>","reason":"<why>"}`
  - 来源: `.cursor/skills/trellis-meta/references/local-architecture/context-injection.md:44-50` + `task-system.md:90-104`
  - 支持 directory 类型: `{"file":"<dir>/","type":"directory","reason":"..."}` (hook 自动读该目录所有 .md)
    - 来源: `.claude/hooks/inject-subagent-context.py:226-243 read_jsonl_entries`
- 注入两条路径 (来源 context-injection.md:33-40 + configurators/shared.ts:575-600 buildPullBasedPrelude):
  - **hook push** (有 hook 平台: claude/cursor/...): PreToolUse(Task) 拦截, hook `inject-subagent-context.py` 读 jsonl → 拼成 `=== {file} ===\n{content}` → 重写 subagent prompt (加 `<!-- trellis-hook-injected -->` marker)。见 inject-subagent-context.py:688-767 main()
  - **agent pull** (无 hook 平台: gemini/qoder/codex/copilot): agent 定义里注入 prelude, 命令 agent 自己 Read `<task>/implement.jsonl` → 逐行 Read。见 trellis-implement.md:19-24 "Trellis Context Loading Protocol" (查 marker 决定 push 还是 pull)
- "决定注入哪些 spec" = **planning 阶段 AI 手工 curate** (task.py create 先种一个 `{"_example":...}` seed 行, planning 步骤 1.3 AI 填真实条目):
  - 来源: workflow.md:381-426 "1.3 Configure context"
  - ready gate: jsonl 至少一条真条目 (seed 行不算), 否则 `task.py start` 报 "planning not ready" (session-start.py:99-120 `_has_curated_jsonl_entry` + workflow.md:424)
  - 发现 spec 路径用 `get_context.py --mode packages` 列包/层
- **monorepo scope**: config.yaml `spec_scope: active_task|list|None`, 按 active task 的 package 过滤注入哪些 spec index (session-start.py:506-562 `_resolve_spec_scope`)
- **check.jsonl 同构**, 只是给 check agent (finish 阶段复用 check.jsonl, inject-subagent-context.py:342-347 get_finish_context)

### skein 现状
- core 层每 session 注入**极简索引** (标题一行), 全文按需 `inject-core`; recall 层 planning 阶段 `recall <query>` 按词检索命中行
- **无 per-task context manifest** — spec 注入靠"core 常驻 + recall grep 召回", 不按 task 显式 curate

### 对比
| 维度 | Trellis (per-task jsonl) | skein (core+recall) |
|---|---|---|
| 精确性 | 高 (task 级显式声明需读哪些 spec) | 中 (recall 按词模糊召回, 可能漏/多) |
| 维护成本 | 高 (每 task planning 多一步 1.3 curate jsonl) | 低 (sediment 一次写, recall 自动检索) |
| token 效率 | 高 (只注入该 task 相关, 无关 spec 不进上下文) | 中 (core 常驻占预算, recall 检索可能不准) |
| 长尾覆盖 | 依赖人 curate, 易漏 | recall grep 覆盖全库 |

### 借鉴价值: 中-高
**一句话建议**: skein 可加**可选 per-task context manifest** (`context.jsonl` 或轻量 `.skein/task/<id>/context.md` 的 frontmatter `inject:` 段), planning 阶段 recall 召回 + 人手补关键 spec, exec dispatch prompt 时显式注入。**不建议全盘照搬 jsonl** (skein 的 recall 已覆盖长尾, jsonl 只补"必读清单"精准度)。

---

## 维度 2: journal (workspace 记忆)

### Trellis 做法
- 路径 `.trellis/workspace/<developer>/journal-N.md`, 每 journal max 2000 行 (config `max_journal_lines`) 自动滚动 (workspace-memory.md:34-46)
- 记录: 每次会话完成的或部分完成的工作, `add_session.py --title --summary --commit` 写入 (workflow.md:78-87)
- **per-dev 非冲突**: `.trellis/.developer` 存当前 dev 身份 (init_developer.py 创建), 每个 dev 一个子目录, 互不干扰 (workspace-memory.md:24-31)
- **与 spec/task 区分** (workspace-memory.md:50-58):
  - task = 本任务的需求/设计/状态
  - workspace journal = 跨任务跨会话的"发生了什么"
  - spec = 长期工程约定
- **commit 分离**: finish-work 分三段 commit: work commits (Phase 3.4) → `chore(task): archive` → `chore: record journal` (finish-work.md:66, workflow.md:588-638)
- **v0.6 加 mem**: `trellis mem` 直接读 `~/.claude/projects/`+`~/.codex/sessions/` 原始对话 JSONL, 按 phase 切片检索 — journal 是"手写摘要", mem 是"原始对话检索", 互补 (session-insight skill + meta SKILL.md:10-18)
- SessionStart 注入 journal 行数 (`Journal: <path>, N/2000 lines`, session-start.py:643-649)

### skein 现状
- **无 journal 概念**。task 自带 `prd/design/findings/research/`, finish 后整体归档 (含 research/ 过程笔记)
- 跨会话记忆只有 spec (core+recall) + task 归档
- 无 per-dev 身份 (默认单仓单人, worktree 隔离按 task 不按人)

### 对比 / 借鉴价值: 中
**一句话建议**: skein 的 task 归档目录已近似"task 级 journal", **缺的是"跨任务会话流水"**。若团队多 dev 场景, 可考虑加 `.skein/workspace/<dev>/` 但 skein 定位单人优先, **暂不建议** (YAGNI); **mem 那套"读原始对话 JSONL 跨会话检索"对单人也有价值**, 可作为可选 skill (读 `~/.claude/projects/` 历史)。

---

## 维度 3: 跨 17 平台

### Trellis 做法 (来源: platform-map.md + platform-files/overview.md + configurators/shared.ts)
- **同一份 .trellis/ 真值**, 17 个平台目录各自适配 (`.claude/.cursor/.codex/.opencode/.kiro/.gemini/.qoder/.codebuddy/.github/.factory/.pi/.reasonix/.kilocode/.agent/.devin/.zcode/.grok`)
- **三种集成模式** (overview.md:22-48):
  1. **Hook/Extension driven** (claude/cursor/codex/opencode/kiro/gemini/qoder/codebuddy/copilot/droid): session-start + workflow-state + inject-subagent-context hooks 主动注入
  2. **Agent prelude / pull-based** (gemini/qoder/codex/copilot 无 hook 改 prompt 能力): agent 定义里塞 prelude 命令 agent 自己读 (buildPullBasedPrelude, shared.ts:586-615)
  3. **Main-session workflow** (kilo/antigravity/devin 无 subagent): 靠 workflow/skill/commands 引导主会话直接读文件跑脚本
- **平台差异抽象**: hook 脚本里 `_detect_platform` 按 env var (`CLAUDE_PROJECT_DIR` 等) + script path 判平台, 统一处理 (inject-subagent-context.py:82-113, session-start.py:186-219)
- **subagent dispatch 协议多格式**: hook 输出同时含 `hookSpecificOutput`(claude/droid) + `permission`/`updated_input`(cursor) + `updatedInput`(gemini), 各平台取自己认识的字段 (inject-subagent-context.py:748-766)
- **template-hash 防覆盖**: `.trellis/.template-hashes.json` 记每文件 hash, `trellis update` 检测用户改过的不强覆盖 (generated-files.md:50-60)
- **shared skill 层 `.agents/skills/`**: codex+gemini 共享同一 skill root (platform-map.md:70-72)
- **bundled skills 自动分发**: `getBundledSkillTemplates()` 从 `templates/common/bundled-skills/` 列目录, 所有平台 skill root 各拷一份 (bundled-skills.md:30-72)
- **平台能力降级**: `[Claude Code, Cursor, ...]` vs `[codex-inline, Kilo, ...]` 在 workflow.md 用 tag 块按平台组分发不同指令 (workflow.md:275-289, 356-434)

### skein 现状
- **仅 Claude Code** (plugin.json hooks + .claude/ 约定)
- 单平台, 无跨平台抽象层

### 对比 / 借鉴价值: 低 (对 skein 当前定位)
**一句话建议**: skein 定位 Claude Code 插件, 跨平台非目标。**若未来想跨**, Trellis 的"共享 .trellis/ 真值 + 平台目录适配 + hook/prelude/workflow 三模式降级"是成熟范本; **`_detect_platform` 按 env var 判平台** + **template-hash 防覆盖**两机制值得记。当前不建议投入。

---

## 维度 4: 4 阶段门控 + verify 自修复

### Trellis 做法 (workflow.md 全文)
实际是 **3 阶段** (Plan/Execute/Finish), README 说 4 阶段是把 verify 拆出:
- **Phase 1 Plan** 入口: `task.py create` (status=planning); 出口: `task.py start` (status=in_progress)
  - 门控: 1.0 create (once) → 1.1 brainstorm 写 prd (repeatable) → 1.2 research (optional) → **1.3 configure context** (curate jsonl, once, ready gate) → 1.4 activate (review gate, once)
  - lightweight task 可只 prd.md; complex task 必须 prd+design+implement+jsonl curated (workflow.md:312-465)
- **Phase 2 Execute**: 2.1 implement (dispatch trellis-implement, no git commit) → 2.2 quality check (dispatch trellis-check) → 2.3 rollback (on demand)
- **Phase 3 Finish**: 3.2 debug retrospective (on demand, break-loop skill) → **3.3 spec update (required once)** → 3.4 commit (required once, AI 驱动 batched commit + 用户一次性确认) → 3.5 wrap-up reminder (跑 /finish-work)
- **每轮 breadcrumb**: `inject-workflow-state.py` 解析 workflow.md 的 `[workflow-state:STATUS]` tag, UserPromptSubmit 每轮注入对应块 (no_task/planning/in_progress/completed), workflow.md 是**唯一真值**, hook 纯 parser 无 fallback (inject-workflow-state.py:174-197)
- **verify 自修复**: trellis-check agent **有 Write/Edit**, "Fix issues yourself, don't just report" (trellis-check.md:43-47, build_check_prompt:416-418) → 自修后重跑 lint/typecheck (check.md:80-85)
- **final pass**: 最后一次 2.2 必须 full-scope (所有 affected package), 不是只查最新 chunk (workflow.md:556)
- **回滚**: 2.3 check 发现 prd defect → 回 Phase 1 改 prd 重做 2.1

### skein 现状
- 4 阶段 plan→exec→check→finish (plan 含 grill 硬门 + memory recall; check 派 checker fan-out + 第 3 轮根因复盘; finish 派 finisher + sediment + commit→merge→archive)
- check: 孤立失败定点修 / 跨 subtask 冲突深化拆分; 第 3 轮 FAIL 走 5 维根因复盘
- **比 Trellis 更重**: grill 对抗审查硬门 + 契约锁定 + subtask DAG 调度 + 根因复盘协议 + sediment 判定门

### 对比 / 借鉴价值: 中
| 点 | Trellis | skein | 谁强 |
|---|---|---|---|
| planning 门 | brainstorm + jsonl ready gate | grill 硬门 + 契约 + DAG | skein 更严 |
| verify 自修 | check agent 有 Write 自修重检 | checker 只读, 派 executor 修 | Trellis 更顺 (少一轮往返) |
| 反复失败 | break-loop skill (debug 后分析) | 第 3 轮 5 维根因复盘协议 | skein 更结构化 |
| breadcrumb | workflow-state 每轮注入 (parser-only) | user-prompt hook 注入 task 判定 | 平手 |

**一句话建议**: **Trellis 的 "checker 自己有 Write 自修"比 skein 的 "checker 只读 + 回派 executor" 少一轮往返**, 但 skein 现设计是有意隔离 (checker 纯验证防越界)。可考虑: **checker 在"孤立失败 + 修复范围明确"时授权直接改** (Trellis 模式), 跨 subtask 冲突才回 plan 拆 — 这正是 skein 现有"孤立失败定点修"的演进方向, 只是把定点修从"回派 executor"改成"checker 自带受限 Write"。

---

## 维度 5: trellis-update-spec (finish 学回写)

### Trellis 做法 (trellis-update-spec/SKILL.md 全文 356 行)
- **触发**: finish Phase 3.3 (required once) — 每个 task finish 前必走, 即使结论是"nothing to update" 也要走完判断 (workflow.md:579-586)
- **code-spec first 原则**: spec = 可执行契约 (签名/payload/env key/边界行为/可测验证错误), 非原则性文字 (SKILL.md:14-22)
- **强制 7 段模板** (infra/跨层契约改动必须): Scope/Trigger → Signatures → Contracts → Validation&Error Matrix → Good/Base/Bad Cases → Tests Required → Wrong vs Correct (SKILL.md:31-41, 148-178)
- **分类决策** (SKILL.md:96-117): Design Decision / Project Convention / New Pattern / Forbidden Pattern / Common Mistake / Gotcha → 各有对应 spec 段 + 模板
- **code-spec vs guide 二分** (SKILL.md:72-91):
  - code-spec (`<layer>/*.md`): "how to implement" 具体签名契约
  - guide (`guides/*.md`): "what to consider" 思考 checklist, 短, 指向 spec
- **update 流程**: identify what learned → classify type → read target spec (防重复) → make update (specific/why/contracts/code/short) → update index
- **break-loop 联动**: debug 后用 break-loop 深分析, 常产出 spec update 需求 (SKILL.md:333-345)
- **finish prompt 也带 spec sync**: build_finish_prompt:443-450 "Analyze whether changes introduce new patterns... if new pattern found: read target spec → update → update index"

### skein 现状
- **sediment 判定门** (sediment-workflow.md): 5 正向触发 (新契约/踩坑≥2轮/反复≥2task/跨任务复用决策/验收基准) + 3 排除 (一次性 bug/私有细节/已有覆盖)
- 判定通过 → 分层 (core 常驻 / recall 按需) → 归类 (类目) → 自动写盘 (不逐次询问)
- **无强制模板**, 沉淀正文写"根因契约 (MUST/禁)"非流水账 (root-cause-protocol.md:53)
- core/recall 两层 + 类目子目录 + 三份索引, vs Trellis 单层 spec + guides 二分

### 对比 / 借鉴价值: 高
| 点 | Trellis update-spec | skein sediment |
|---|---|---|
| 强制结构 | 7 段模板 (契约类) + 6 类分类 | 无模板, 靠判定门筛 |
| 可执行性 | code-spec (签名/契约/错误矩阵) 强 | "根因契约 MUST/禁" 偏软 |
| 触发 | 每 task finish 必走判断 | 判定门通过才写, 全无增量跳过 |
| 分层 | 单层 + guide/spec 二分 | core/recall 两层 + 类目 |
| 写盘 | 手工 edit spec 文件 | sediment 命令自动写+reindex |

**一句话建议**: skein 可借鉴 Trellis 的 **(a) code-spec 7 段强制模板** 用于"契约/接口/跨层"类 sediment (现 skein 沉淀正文无结构约束易写虚); **(b) code-spec vs guide 二分** —— skein 可在 recall 层细分"契约型"(签名/错误矩阵, 强结构) vs "经验型"(选型/踩坑, 自由文本), 提升注入可执行性; **(c) 每 task finish 必走判断** (skein 现已是, 但可显式化: 即使 drop 也要输出一句 trace)。skein 的 core/recall 两层 + 自动写盘 reindex 比 Trellis 单层手工 edit **更先进**, 不必回退。

---

## 维度 6: trellis-research sub-agent

### Trellis 做法 (.claude/agents/trellis-research.md 全文)
- **职责单一**: "find, explain, and PERSIST information" — 只调研不改码 (research.md:13-16)
- **核心原则**: 对话会被压缩, 文件不会 → 每个调研产出 MUST 落 `{TASK_DIR}/research/<topic>.md`, 只回 chat 算失败 (research.md:17-18)
- **scope 限制** (research.md:64-79):
  - Write ALLOWED: 只 `{TASK_DIR}/research/*.md`
  - Write FORBIDDEN: 代码 / spec (那是 update-spec 的事) / scripts / workflow / platform config / 其他 task 目录 / 任何 git 操作
- **workflow** (research.md:30-61):
  1. `task.py current --source` 解析当前 task 路径 (无 active task 则问用户, 禁猜)
  2. classify (internal/external/mixed) + scope
  3. 并行搜索 (Glob+Grep+web)
  4. 每主题写一个 `research/<topic>.md` (固定 frontmatter: Query/Scope/Date + Findings/Files Found/Code Patterns/External Refs/Related Specs/Caveats)
  5. 回 main: **只回文件路径 + 一行摘要 + 关键 caveat**, 禁贴全文
- **hook 注入**: inject-subagent-context.py:738-741 对 research agent 注入 spec 目录树概览 (动态发现 spec dirs), 不注入 prd/jsonl (research 不依赖 active task)
- **边界**: 用户让改代码 → 拒绝, 建议派 implement (research.md:78-79)

### skein 现状 (skein-researcher agent)
- **几乎一致**: 只读 (无 Write/Edit, 唯一例外 research/ 落盘) + Recursion Guard + 带来源 + 不替用户决定
- 落盘 `.skein/task/<id>/research/<topic>.md`, 回传压缩版
- **多一个 bootstrap 扫描模式** (冷启动播种, 扫五维提炼候选规则)
- 绑定 skein-research skill (agent-reach 优先探测的外部检索分层)

### 对比 / 借鉴价值: 低 (skein 已对齐甚至更全)
**一句话建议**: skein-researcher 与 trellis-research 设计高度一致 (都只读+落盘+回压缩), skein **还多了 bootstrap 扫描模式 + agent-reach 多平台检索分层**, 不需借鉴。唯一可选: Trellis 的固定 file format (Query/Scope/Date + Findings 表格) 可作为 skein-researcher 落盘模板参考, 提升一致性。

---

## 维度 7: scoped specs vs monolithic

### Trellis 做法 (spec-system.md + .trellis/spec/ 实际结构)
- **scoped = 按 package × layer 分子目录** (spec-system.md:6-40):
  - 单仓: `spec/{backend,frontend,guides}/`
  - monorepo: `spec/{<package>}/{<layer>}/` (如 `spec/cli/backend/`, `spec/docs-site/docs/`)
- **每层 index.md = 入口**: 列 Pre-Development Checklist + Quality Check + 指向具体 guideline 文件 (spec-system.md:42, 实例见 .trellis/spec/cli/backend/index.md)
- **guides/ 跨包思考 checklist** (cross-layer/code-reuse/cross-platform thinking guides)
- **包配置** (config.yaml): `packages: {<name>: {path, type}}` + `default_package` + `spec_scope` (active_task|list|None 控制注入范围)
- **注入粒度**:
  - SessionStart: 只注入 spec **index 路径列表** ("Available indexes", session-start.py:795-799), 不注入全文
  - subagent: jsonl 显式声明该 task 需读哪些 spec 文件/目录 (维度 1)
  - AI 按需 Read index → 跟链接读具体 guideline (before-dev skill:24-31)
- **registry 刷新** (v0.6): config `registry.spec.source` 可从外部 registry 刷新 spec (meta SKILL.md:67-68)
- **vs monolithic (CLAUDE.md/AGENTS.md)**: README FAQ 明确 "those files tend to become monolithic, Trellis adds scoped specs" — 拆分 + 按需注入解决单文件臃肿

### skein 现状
- **两层 × 类目**: core/{类目}/*.md + recall/{类目}/*.md, 类目 = git/test/arch/build/style/domain/ops
- 三份索引 (每层 index + 顶层聚合), sediment 写盘自动 reindex
- SessionStart 注入 core **极简索引** (标题一行), 全文按需 inject-core; recall 按词检索

### 对比 / 借鉴价值: 中
| 点 | Trellis scoped | skein 两层×类目 |
|---|---|---|
| 分层依据 | package × layer (代码结构) | core/recall (注入时机) × 类目 (领域) |
| 索引 | 每 layer index.md (Checklist+QC) | 三份 index (标题聚合) |
| 注入 | per-task jsonl 显式 + SessionStart index 路径 | core 极简索引 + recall grep |
| monorepo | 原生 packages 配置 | 无 (单仓) |
| spec 内容结构 | index 含 Pre-Dev Checklist + Quality Check 段 | 自由格式 |

**一句话建议**: **(a) skein spec index.md 可借鉴 Trellis 的"Pre-Development Checklist + Quality Check"结构段**, 让每条 core 规则不光是"契约"还带"何时查/怎么验"指针, 提升注入后可操作性; **(b) 若 skein 未来支持 monorepo, Trellis 的 packages + spec_scope(active_task) 按 task package 过滤注入是范本**; **(c) Trellis 的"index 只列路径不注入全文, AI 按需读"与 skein "core 极简索引 + inject-core 按需拉"理念一致**, skein 已对齐, 无需改。skein 的 **core/recall 两层注入时机分层**比 Trellis 单层 + 手工 jsonl curation **更自动**, 是 skein 差异化优势。

---

## 汇总: 借鉴优先级排序

| 优先级 | 借鉴点 | 来源维度 | 预期收益 |
|---|---|---|---|
| 高 | code-spec 7 段强制模板 (契约类 sediment) | 维度 5 | 沉淀正文从软契约→可执行契约 |
| 高 | code-spec vs guide 二分 (recall 细分契约型/经验型) | 维度 5 | 提升注入可执行性 |
| 中-高 | 可选 per-task context manifest (补 recall 精准度) | 维度 1 | exec 注入更精确 |
| 中 | checker 孤立失败时授权直接 Write 自修 (Trellis 模式) | 维度 4 | 少一轮 exec 往返 |
| 中 | spec index 加 Pre-Dev Checklist + Quality Check 段 | 维度 7 | 注入后可操作性 |
| 中 | journal/跨任务会话流水 (仅多 dev 场景) | 维度 2 | 团队场景记忆 |
| 中 | mem 式读原始对话 JSONL 跨会话检索 (可选 skill) | 维度 2 | 单人也有价值 |
| 低 | 跨平台抽象 (非 skein 目标) | 维度 3 | 当前不投入 |
| 低 | researcher 固定 file format 模板 | 维度 6 | skein 已对齐 |

## 不建议借鉴 (skein 已更优)
- core/recall 两层 + 自动写盘 reindex > Trellis 单层手工 edit spec
- grill 硬门 + 契约锁定 + DAG 调度 > Trellis brainstorm + jsonl gate (skein 更严)
- 第 3 轮 5 维根因复盘 > Trellis break-loop (skein 更结构化)
- bootstrap 冷启动播种 + agent-reach 多平台检索 > Trellis research (skein 更全)
