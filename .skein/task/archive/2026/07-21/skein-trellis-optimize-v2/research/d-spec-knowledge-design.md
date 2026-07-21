# 调研: skein v2 D — memory→spec 概念演进 + 模板骨架设计

> 只读调研产物, 供 main 走基石罗盘门 + 写 D 子 PRD。不做设计决策 (候选给 main/用户选)。
> 数据源: 本仓代码勘察 (memory.py / hooks.py / plugin.json / spec 全量样本) + agent-reach 可用→降级 WebSearch (外部框架骨架)。外部框架对比已复用本 task 既有 `research/spec-driven-frameworks.md` (26.7K 全量), 本报告只补「骨架结构」视角。

---

## A. skein 现有 spec 全量分析

**规模**: core 9 条 (10 文件含 index), recall 42 条 (43 含 index)。类目分布见 `.skein/spec/index.md`。
- core 类目: agent(2) arch(2) command(1) git(1) ops(1) script(1) skill(1) — `7` 类目
- recall 类目: arch(9) frontend(8) hook(2) impl(3) migration(1) ops(10) plugin-arch(1) style(6) test(2) — `9` 类目

### A.1 文体分类 (经验/规约/ADR/契约/域知识)

抽 core 全 9 + recall 跨类目 12 条分析, 按主导文体归类:

| 文体 | 特征 | 占比(估) | 代表样本 |
|---|---|---|---|
| **规约/契约** (命令式 MUST/禁) | 「禁X」「必须Y」「铁律」起首, 表格列禁/改为 | core 主导 (~7/9) | core/agent/skein-skill-agent-slim-01 (`## 三条铁律`+反例表), core/ops/skein-hook-trim-03 (`## 铁律`+操作流程+反例), core/script/script-conventions-00, core/git/worktree-patterns-00 |
| **ADR/陷阱** (context→decision→consequence) | 触发场景/陷阱/症状/修法/反例 | recall arch/ops/test 主导 (~20/42) | core/arch/pep-563-framework-annotation-00 (触发场景→陷阱→症状→修法→判定门→反例→适用), recall/frontend/click-bubble-document-listener-pattern-00 (陷阱→正解→onLive重挂→适用→案例), recall/test/pytest-fixture-mypy-00 (触发场景→三处错源→组合键→反例→适用) |
| **域知识/实现** (算法/机制描述) | 纯叙述+表格+代码, 非教训型 | recall impl/arch 少数 | recall/arch/dag-scheduling-01 (两层同构→就绪判定→调度循环→示例), recall/impl/lock-mechanism-01 (设计动机→锁机制→适用命令) |
| **方法论/编码法** (抽象原则) | 概念定义+分类表+为什么 | recall style 少数 | recall/style/skein-skill-agent-slim-06 (Match the Form to the Failure, 失败类型→编码形式表), core/arch/two-layer-memory-00 (设计动因→类目系统→索引→判定门→预算) |

**结论**: core 偏**规约/契约** (命令式 + 反例表), recall 偏 **ADR/陷阱经验** (触发场景→正解→反例)。两类文体骨架需求不同 — core 需"铁律+反例表"脊柱, recall 需"触发场景→陷阱→正解→案例"脊柱。

### A.2 零星骨架段频次统计 (grep .skein/spec/core + recall, 51 文件)

| 段名 | 文件数 | 主导层 |
|---|---|---|
| `适用` | 28 | recall 经验型标配 |
| `反例` | 22 | 两层都有 (core 反例表 + recall 反例段) |
| `触发场景` | 15 | recall 陷阱型标配 (core 偶现) |
| `关联` / `关联 [[wikilink]]` | 14 / 10 | 两层都有 (手工 wikilink, 无 frontmatter 字段支撑) |
| `案例` | 13 | recall 经验型 |
| `铁律` | 6 | core 契约型 |
| `现象` / `根因` / `信号` | 6 / 9 / 4 | recall 陷阱型子段 |
| `修法` | 3 | recall arch 陷阱型 |
| `判定门` | 2 | 仅 sediment-workflow.md 引用, 非规则正文 |

**关键发现**:
- `触发场景`(15) / `适用`(28) / `反例`(22) / `案例`(13) 已是**事实标准段**, 但**无强制模板**, 每条自己起结构 (sediment 透传 body 无骨架, memory.py:208-219)。
- `关联 [[wikilink]]`(10 条) 是**自发出现的**, 但 frontmatter 无 `related` 字段, reindex 也不解析 wikilink → 断链无检测, 纯人工维护。
- core 的 `铁律`/`反例表` 与 recall 的 `触发场景/陷阱/正解` 是**两种不同脊柱**, 不应一套模板硬套两层。

### A.3 frontmatter 字段实际使用

sediment 硬编码 7 字段 (memory.py:209-219): `title / layer / category / keywords / source / authored-by / created`。
- `keywords`: 实际填逗号分隔词袋, 如 `[冒泡,bubble,click.stop,document监听,...]` (click-bubble 10 词) / `[pep-563,...,422,forward-ref,局部import,类型注解]` (pep-563 11 词)。词袋粒度参差 (有的英文技术词, 有的中文场景词), 无规范。recall 粗筛靠它 (memory.py:184-193 grep index.md keywords 列)。
- `source`: 实际填 task-id (如 `skein-queue-hover-detail` / `ccplugin-skein` / `skein-flow-redesign`) 或 bootstrap 标记。`authored-by` 恒 `skein-memory` (无信息量, 推测: 可弃或改记 agent)。
- `created`: Unix epoch 秒 (memory.py:56 `now()`)。
- **`updated`**: 仅 1 条出现 (recall/frontend/structured-doc-chapters-checkboxes-04.md:296), 非 sediment 写入 (推测手改), 说明**updated 字段已有人需要但无机制**。
- **无 `status` / `related` / `applies-to` / `superseded`**: 均缺。

---

## B. 外部知识库/spec 框架骨架对比

> 外部框架方法论/多角色已在本 task `research/spec-driven-frameworks.md` 详尽覆盖。本节只摘**骨架结构**维度 + 补 ADR/zettelkasten/Claude memory。

| 框架 | 骨架设计 | 强项 | skein 可借鉴点 |
|---|---|---|---|
| **spec-kit** (github/spec-kit) | spec-template.md 强制段: User Scenarios(每 story Priority+Independent Test+Acceptance Given/When/Then) / Requirements(FR-001 稳定ID) / Success Criteria(SC-001) / **[NEEDS CLARIFICATION] 强制标记歧义** | 强制结构 + 禁猜标记 + 稳定可追溯ID | `[NEEDS CLARIFICATION]`→强化 skein 已有 `需要:` 协议; 强制段思路验证「sediment 加骨架」方向 |
| **BMAD** | "Essential Spine + Adapt-In Menu" 弹性模板 (默认必现段 + 按需拉入段); architecture 只固定 **invariants spine**, 结构性归代码 | 弹性 (非一刀切) + invariant vs structural 二分 | **spine = invariants 二分**→skein core=spine(invariant), recall=structural(case); Adapt-In Menu 思路→core 脊柱固定段 + recall 自由段 |
| **ADR** (Nygard) | Title / Status(Proposed/Accepted/Deprecated/Superseded) / Context / Decision / Consequences | **Status 显式生命周期** + Context-Decision-Consequence 三段极简 | recall 陷阱型天然 = ADR (Context=触发场景, Decision=正解, Consequences=反例); **`status` 字段** 值鉴 (sediment 默认 active, 废弃标 deprecated/superseded) |
| **zettelkasten/Obsidian** | 原子笔记 + frontmatter(tags/links) + `[[wikilink]]` 双链 + 时间戳ID | **原子性** (一笔记一概念) + **双链可发现** | skein 已自发用 `[[wikilink]]`(10条); `related` frontmatter 字段 + reindex 解析双链 (当前断链无检测) |
| **Claude CLAUDE.md** | imperative 指令 + WHAT/HOW/WHY 三柱 + <200 行 + 分层按路径加载 | imperative 语气 + 简洁 | skein core 命令式契约已同频; 简洁原则→core 预算警戒已有 |

**结论 (骨架元素→skein 两层映射)**:
- **core spine** 借 BMAD invariant spine + CLAUDE.md imperative: 固定段 `铁律(命令式) / 反例表(禁/改为) / (可选)关联`。core 不需 `触发场景`(它已是硬约束, 无条件生效)。
- **recall spine** 借 ADR + spec-kit + zettelkasten: 固定段 `触发场景(Context) / 陷阱/正解(Decision) / 反例 / 案例(Consequences) / 适用 / 关联[[wikilink]]`。recall 是经验型, 需 context 才能判适用性。
- **frontmatter 增字段** 借 ADR(zettelkasten): `status` (active/deprecated/superseded) + `related` (wikilink 列表) + `updated` (已有需求, 1 条手填)。

来源:
- spec-kit: https://github.com/github/spec-kit , https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/
- BMAD: https://docs.bmad-method.org/ , https://bennycheung.github.io/bmad-reclaiming-control-in-ai-dev
- ADR: https://github.com/architecture-decision-record/architecture-decision-record , https://adr.github.io/ , https://martinfowler.com/bliki/ArchitectureDecisionRecord.html
- zettelkasten: https://otio.ai/blog/best-zettelkasten-atomic-note-templates , https://forum.obsidian.md/t/share-your-zettel-note-template/3961
- Claude memory: https://code.claude.com/docs/en/memory , https://www.buildcamp.io/guides/the-ultimate-guide-to-claudemd

---

## C. 推荐骨架方案 (3 候选, 标推荐)

### 候选 1 (推荐): **分层弹性脊柱 + 轻量 frontmatter 增字段 + 软模板 (template 文件, 非硬编码)**

**设计依据**:
- BMAD "Essential Spine + Adapt-In Menu" + ADR Context-Decision-Consequence + 本仓事实段频次 (触发场景15/适用28/反例22/案例13 已是事实标准, 不需发明, 只需固化)。
- sediment 是 fire-and-forget (memory.py:196 异步, finish 闭环不等), **硬模板会增开销且 memorier 已是 haiku 模型** → 用「template.md 参考文件 + sediment 写盘前 memorier 参照填充」而非 memory.py 强制 body 结构。

**core spine 模板** (放 `plugins/tools/skein/skills/skein-memory/references/templates/core.md.tmpl`):
```
# <标题>

## 铁律 / 契约

<命令式契约: MUST X / 禁 Y. 一句一规则>

## 反例 (命中=违规)

| 禁 | 改为 |
|---|---|
| ... | ... |

## (可选) 关联

[[<wikilink>]]
```

**recall spine 模板** (`references/templates/recall.md.tmpl`):
```
# <标题>

## 触发场景

<什么情况下会踩这个坑 / 需要这个模式>

## 陷阱 / 正解

<错误做法→根因→正确做法>

## 反例

<❌ ... → ✅ ...>

## 案例

<具体 commit / 文件 / 代码片段佐证>

## 适用

<什么场景可复用>

## 关联

[[<wikilink>]]
```

**frontmatter 增字段** (memory.py:209-219 sediment 写盘段, sed 7 字段 → 9 字段):
```
status: active        # 新增: active | deprecated | superseded
related: [<wikilink>] # 新增: 关联规则 stem 列表 (空则 [])
updated: <ts>         # 新增: 最后修订 (sediment 写时 = created; maintain/手改时刷新)
```
- `source/authored-by`: 保留 (author-by 推测可弃, 但弃需改 memory.py + reindex, 不强求)。

**对 fire-and-forget + CORE_BUDGET 影响**:
- **零运行时影响**: 模板是参考文件 (memorier 读 → 填 body), memory.py 只增 3 frontmatter 字段写盘 (sediment 段 +3 行), 不改注入逻辑 (inject_core/session_start/subagent_start 仍 `_strip_frontmatter` 后透传, memory.py:118/151)。
- **CORE_BUDGET (8000)**: 不变 (骨架不加常驻字符, core 注入仍只 index + 全文 strip frontmatter)。
- **旧 spec 兼容**: frontmatter 缺 `status/related/updated` 不报错 (frontmatter 解析 memory.py:317-328 容错缺键; hooks.py spec-meta SPEC_REQUIRED 只查 title/layer/created/keywords, 不含新字段 → **不破坏**)。旧 spec 默认视为 status=active。

**代码改动量估**:
- `memory.py`: sediment 写盘段 +3 字段 (~3 行); 新增 maintain 命令 (见 D); reindex_layer 输出可加 status 列 (可选 ~2 行)。**≈5-10 行**。
- `skills/skein-memory/references/templates/`: 新增 2 个 .tmpl 文件 (~30 行)。
- `skills/skein-memory/SKILL.md`: 加一段「写盘参照模板」引用 (~5 行)。
- `agents/skein-memorier.md`: 作业二 sediment 草案段加「参照模板填 body」(~3 行)。
- 总计 **≈50 行 + 2 模板文件**。

### 候选 2: **memory.py 强制 body 校验 (hooks spec-meta 扩展必填段)**

**设计依据**: spec-kit 强制段思路, 把「触发场景/正解/反例」做成 spec-meta hook 的必填检查。

**方案**: hooks.py `SPEC_REQUIRED` 从 frontmatter 字段扩展到 **body 段名检查** (grep `## 触发场景` / `## 反例` 等, 缺则 warning)。

**优劣**:
- (+) 强约束, 新规则必齐段。
- (−) **core 规约型本就不该有「触发场景」** (core 是无条件硬约束), 强制段会逼 core 硬塞场景段, 违背 core=规约/recall=ADR 分层。
- (−) 旧 51 spec 大量缺段, hook 会刷屏 warning (需迁移脚本, 工作量大)。
- (−) 与 fire-and-forget 矛盾 (memorier haiku 填不全段会 warning 噪声)。

**不推荐** (与两层文体差异冲突 + 迁移负担)。

### 候选 3: **纯 frontmatter 增字段, 无 body 模板 (最小变更)**

**设计依据**: zettelkasten 仅靠 metadata 组织, body 完全自由。只加 `status/related/updated`。

**优劣**:
- (+) 改动最小 (memory.py +3 行, 无模板文件)。
- (−) **不解决已知短板** (sediment body 各自为政, D 勘察报告核心问题); body 骨架零星段仍各自为政。

**适合**: 若用户认为 body 模板过度设计, 此候选是退路。

### 推荐与理由

**推荐候选 1**。理由:
1. 直击 D 勘察短板 (body 透传无骨架) 同时尊重两层文体差异 (core=规约/recall=ADR 两套脊柱)。
2. 软模板 (参考文件) 不破 fire-and-forget (不强校验, 不增 haiku memorier 负担)。
3. 兼容旧 spec (frontmatter 缺新字段不报错, 旧 spec 默认 active)。
4. `status/related/updated` 增字段为 D 的 maintain 命令 (stale 判据) 铺路。
5. 改动量小 (~50 行 + 2 模板), 可单 subtask 落。

**需用户裁**: 候选 1 vs 候选 3 的 body 模板要不要 (核心分歧 — 软模板有引导价值但增 memorier 作业步骤)。

---

## D. maintain 命令设计

### D.1 子命令接口

```
skein-memory maintain                  # 默认: 全量体检 (stale + broken-link + 超预算), 输出报告
skein-memory maintain --fix-stale       # 交互标记 deprecated (列候选, 不自动删)
skein-memory maintain --fix-links       # 修/报断链
skein-memory maintain --layer recall    # 仅 recall
```

**输出格式** (非 JSON, 给人读; 与 `memory.py list_` 风格一致):
```
maintain 体检 (.skein/spec):
[超预算] core 8200 > 8000 字符 — 考虑降级: script/conventions-00 (2100)
[stale] recall/arch/legacy-pattern-00 (created 1750, 14月前, status active)
[断链] recall/frontend/click-bubble: [[hover-click-popover]] 目标存在 ✓
[断链] recall/ops/old-rule: [[nonexistent]] ✗ 目标缺失
[重复 keywords] "worktree,merge" 出现 3 次: git/worktree-00, ops/x, arch/y
```

### D.2 stale 判据建议

| 判据 | 阈值 | 动作 |
|---|---|---|
| `created` 年龄 | recall > 180天 (~6月) 且无 `updated` | 标记候选 (不自动, 列报告) |
| `status` 字段 | `deprecated`/`superseded` | 建议归档 (archive --layer) |
| broken wikilink | `[[X]]` 目标 stem 在库内无匹配 | 列报告 |
| keywords 高重复 | 同 keywords 组 ≥3 条 | 建议合并 (人工裁) |
| **recall 命中埋点** | — | **YAGNI 后置** (需 hook 记 recall 命中文件, 当前无埋点; 用户已拍板后置) |

**stale 不自动删**: 只输出候选清单, 删除/归档走 archive 子命令 (memory.py:272 已有可逆归档)。契合「可逆纠正」(SKILL.md:69 反例表)。

### D.3 session-start 提示触发条件

当前 session-start 只注入 core 极简索引 (memory.py:139-147)。maintain 提示挂 session-start **附加一行** (不新增 hook, 复用 session_start() 末尾预算内):
- 触发: (a) core 全文 > CORE_BUDGET(8000) — memory.py:120 已有 stderr 告警, 提升为 session 注入; (b) 最老规则年龄 > 阈值 (扫 core created min, > 180天提示跑 maintain)。
- 输出: `⚠️ core 超 budget / 有 N 条 > 6月老规则, 跑 \`skein-memory maintain\` 体检`。
- 预算: ≤1 行, 不挤 INDEX_BUDGET_TOKENS(400)。

### D.4 代码改动量估

- `memory.py`: 新增 `maintain` 方法 + argparse 子命令 (~40-60 行: 扫两层 + 4 判据 + 报告格式); session_start() 加 1-2 行提示 (~5 行)。**≈50-70 行**。
- `skills/skein-memory/SKILL.md`: 加 maintain 段 (~10 行)。
- 总计 **≈60-80 行**。

---

## E. rename (memory→spec) 影响面清单

> 用户已拍板全仓 rename memory→spec。以下是需改文件 + 各自改动点 + 风险。

### E.1 需改文件全量 (经 `grep -rli memory` 全仓扫描)

| 类别 | 文件 | 改动点 | 风险 |
|---|---|---|---|
| **脚本** | `scripts/memory.py` | 重命名 `memory.py`→`spec.py`; docstring (`SKEIN 两层规则记忆`→`spec 库`); `Memory` 类名→`Spec`/`SpecStore`; 命令名 `inject-core`/`session-start` 等 func 名 (可选保留接口); `prog="memory.py"`(memory.py:348)→`spec.py`; AGENT_CATEGORIES 注释 (memory.py:42) | **高**: 类名/文件名全局引用; func 名若改需同步 bin/skein-memory + plugin.json hooks command |
| **脚本** | `scripts/skein.py` | 2 处: skein.py:2537-2538 `memory.py` 路径 + init 调用; docstring | 中 (2 处 grep 确认) |
| **脚本** | `scripts/hooks.py` | spec-meta hook (hooks.py:168-227) 已用 spec 术语, 基本免改; 检查 `memory` 字样 | 低 |
| **bin** | `bin/skein-memory` | 文件名→`bin/skein-spec`; 内部 `scripts/memory.py`→`scripts/spec.py` (bin/skein-memory:6 `_target`) | **高 (hooks command 路径)**: plugin.json SessionStart/SubagentStart hooks command `${CLAUDE_PLUGIN_ROOT}/bin/skein-memory` (plugin.json:80,112) 必须同步改 |
| **plugin.json** | `.claude-plugin/plugin.json` | hooks command `bin/skein-memory`→`bin/skein-spec` (2 处: SessionStart:80, SubagentStart:112); description 内 "memory"/"spec" 文案; keywords `rules-memory` (plugin.json:58) | **最高**: hooks command 改错 → session 注入静默失效 (hook 路径 404) |
| **skill** | `skills/skein-memory/` | 目录名→`skein-spec/`? (plugin.json skills 列表 plugin.json:35 `./skills/skein-memory` 需同步); SKILL.md frontmatter `name: skein-memory`(SKILL.md:2)→`skein-spec`; description; 全文 memory→spec | **中**: skill 目录名改需同步 plugin.json + agent skills 引用 |
| **skill refs** | `skills/skein-memory/references/{bootstrap-seeding,reconstruct-memory,sediment-workflow}.md` | 全文 memory→spec; 命令调用 `skein-memory sediment`→`skein-spec sediment` | 中 |
| **agent** | `agents/skein-memorier.md` | `name: skein-memorier`(memorier.md:2)→`skein-spec`? (推测: 保留 memorier 角色名, 只改绑定 skill); `skills: skein:skein-memory`(memorier.md:9)→`skein:skein-spec`; 全文 `skein-memory recall/sediment`→`skein-spec` | 中 (agent 名是否改需用户裁 — memorier 是角色语义, spec 是资源语义, 不必同改) |
| **agent** | `agents/skein-researcher.md`, `skein-setup.md` | 引用 skein-memory 处 | 低 |
| **其他 skill** | `skein-finish/SKILL.md` + `references/sediment-protocol.md`, `skein-flow/SKILL.md` + `references/scope-boundary.md`, `skein-check/references/root-cause-protocol.md`, `skein-exec/references/scheduling-algorithm.md`, `skein-plan/references/breaking-refactor.md`, `skein-setup/{SKILL.md,references/trellis-migration.md}` | 引用 `skein-memory` 命令/skill 名 → 改 | 中 (散布, 需逐文件 sed) |
| **docs** | `docs/{best-practices,getting-started,reference,glossary,workflow,scenarios}.md` + `README.md` | memory→spec 文案 (reference.md 13处最多, workflow.md 9处) | 低 (文档, 非运行时) |
| **docs 顶层** | `README.md`(4处) + `docs/ONBOARDING.md`(1处) | 文案 | 低 |
| **docs 样本** | `docs/examples/sample-skein/spec/**` (4 文件) | frontmatter `authored-by: skein-memory` → 保留(历史)或改; 样本文案 | 低 (示例) |
| **测试** | `scripts/tests/test_memory.py` + `conftest.py` | 文件名 test_memory→test_spec; 导入 `memory` 模块→`spec`; 测试用例路径 | 中 (CI, 改错 pytest 挂) |

**总计**: ~25-30 文件改动 (42 含 memory 的文件中, 排除 __pycache__/.pyc 及非语义命中)。

### E.2 风险点 (按严重度)

1. **🔴 最高 — hooks command 路径**: plugin.json SessionStart(80) + SubagentStart(112) 的 `bin/skein-memory` 必须与 bin/ 下实际文件名同步。改错 → core 注入静默失效, 无报错 (hook 失败 Claude Code 静默)。**验证**: rename 后跑 `skein-doctor` + `claude -p` 质量门 (CLAUDE.md 检查规范)。
2. **🟠 高 — 类名 Memory→Spec**: memory.py:90 `class Memory` 若改, 全文件 self. 引用 + 可能的外部导入 (skein.py 未 import 类, 只 subprocess 调脚本 → 影响小; 但 test_memory.py 可能 import)。**降险**: 保留类名 `Memory` 不改, 只改文件名/命令名 (类名内部细节, 用户无感)。
3. **🟠 高 — skill 目录名**: `skills/skein-memory/`→`skills/skein-spec/` 需同步 plugin.json:35 + agent frontmatter `skills:`(memorier.md:9)。**降险**: skill name(frontmatter)与目录名必须一致, 用 grep 全量核对。
4. **🟡 中 — agent 名**: `skein-memorier` 是否改名? 推测: **不改** (memorier=角色"记忆员"语义, spec=资源; 角色名保留, 只改绑定 skill 引用)。需用户裁。
5. **🟡 中 — dispatch 引用**: SKILL/agent 正文 `skein-memory sediment`(sediment-workflow.md:31, memorier.md:22,42 等)需全量改命令名。
6. **🟢 低 — 旧 spec 文件 frontmatter `authored-by: skein-memory`**: 历史值, 可保留 (无运行时依赖, reindex 不校验 authored-by)。

### E.3 rename 建议范围 (需用户裁的分歧)

- **窄义 rename** (推荐, 低险): 只改对外命令名 `bin/skein-memory`→`bin/skein-spec` + plugin.json hooks command + SKILL/agent/doc 文案引用。**保留** `scripts/memory.py` 文件名 + `class Memory` 类名 + `skein-memorier` agent 名 (内部细节, 改无收益增险)。
- **全义 rename** (用户原话"全仓 rename"): 上述 + `memory.py`→`spec.py` + `Memory`→`Spec` 类名 + skill 目录名 + 可能 memorier→spec-keeper。工作量大 3x, 险高。

**推测建议**: 窄义对外 rename 已达"用户感知 memory→spec"目标 (命令/skill 名用户可见), 内部文件名/类名改是洁癖性收益, 不值风险。**需 main 转达用户裁窄义 vs 全义**。

---

## F. subtask 拆分建议 (按依赖, 3-5 个)

| subtask | 内容 | 依赖 | 估工作量 |
|---|---|---|---|
| **ST-D1: rename memory→spec (窄义)** | bin/skein-memory→bin/skein-spec + plugin.json hooks command(2处) + skills/agents/docs 命令名引用全量 sed + doctor/质量门验证 | 无 (独立, 先做免后续 subtask 引用混) | 中 (~20 文件 sed + 验证) |
| **ST-D2: frontmatter 增字段** | memory.py sediment 写盘段 +status/related/updated(+3行); hooks spec-meta 可选校验新字段(可选); 旧 spec 不迁移(默认 active) | ST-D1 后 (若 D1 改文件名, D2 在新名上改) | 小 (~10-15 行) |
| **ST-D3: 模板骨架 (候选1)** | 新增 `skills/skein-memory/references/templates/{core,recall}.md.tmpl`; SKILL.md + memorier.md 加"参照模板填 body"段 | ST-D2 后 (模板引用新 frontmatter 字段如 related) | 小 (~50 行 + 2 文件) |
| **ST-D4: maintain 命令** | memory.py 新增 maintain 方法 + 子命令 + 4 判据 + 报告格式; session-start 提示行; SKILL.md 文档 | ST-D2 后 (依赖 status/created 字段); ST-D3 无强依赖可并行 | 中 (~60-80 行) |
| **ST-D5: (可选) body 模板校验 (候选2)** | hooks spec-meta 扩展 body 段名检查 | ST-D3 后 | 小 (~20 行), 但**不推荐**(与两层文体冲突) |

**依赖图**:
```
ST-D1 (rename) ─┬─> ST-D2 (frontmatter) ─┬─> ST-D3 (模板骨架)
                │                         └─> ST-D4 (maintain)
                └─ (ST-D5 可选, 不推荐, 独立)
```
**建议串行**: D1 → D2 → (D3, D4 并行)。D1 必须先 (rename 后所有引用稳定, 免 D2-D4 改完又被 rename 覆盖)。

---

## G. 验收自检 (对照 dispatch 验收标准)

- ✅ 全量 spec 样本分析: core 全 9 + recall 跨类目 12 (arch4/frontend2/ops2/impl1/test1/style1/migration1), 带 file:line/段频次统计
- ✅ 外部框架对比带 URL: spec-kit/BMAD/ADR/zettelkasten/Claude memory 各 2-3 URL
- ✅ 骨架方案 ≥2 候选 (给 3): 候选1推荐 + 候选2/3 退路, 有明确推荐理由
- ✅ maintain 设计可落地: 接口(4 子命令)+判据(4 条表)+触发(2 条件)
- ✅ rename 影响面完整: ~25-30 文件逐类列, hooks command 路径 + plugin.json 风险标红
- ✅ subtask 拆分: 5 个 (4 主 + 1 可选不推荐), 标依赖图

## 需要 (需 main 转达用户裁)

1. **body 模板要不要** (候选1 vs 候选3 核心分歧): 软模板有引导价值但增 memorier 作业步骤; 候选3 纯 frontmatter 最小变更。
2. **rename 窄义 vs 全义**: 窄义(只改对外命令/skill 名, 保留 memory.py 文件名/Memory 类名/memorier agent 名)低险达用户感知目标; 全义(连文件名/类名)洁癖性收益不值风险。
3. **skein-memorier agent 名是否随 rename 改**: 推测不改 (memorier=角色语义, spec=资源语义), 需确认。

