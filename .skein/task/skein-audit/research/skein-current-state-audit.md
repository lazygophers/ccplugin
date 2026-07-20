# SKEIN 现状深度审计 (8 维度, 供"学 Trellis 整体优化"基线)

范围: plugins/tools/skein/ 全量。只读审计, 量化数据 + 优化方向。

---

## 1. token 冗余 (跨文件重复同一概念)

SKEIN 的核心约束在 skill/agent/docs **多处反复重述**, 每处措辞略不同 → 维护漂移风险 + 模型加载多份重复 token。统计 (grep -l 命中文件数):

| 重复概念 | 命中文件数 | 主要重复点 |
|---|---|---|
| dispatch 6 字段 / dispatch prompt | 19 | flow(carrier-rules) / exec(scheduling-algo) / 6 个 agent / workflow / best-practices / reference 全各说一遍 |
| sediment 判定门 | 16 | memory SKILL + sediment-workflow + finish SKILL + finisher + workflow + docs/README + reference + best-practices |
| Recursion Guard / 递归护栏 | 14 | 每个 agent 各写一段 + flow + workflow + glossary + reference |
| check 回 planning 重确认 | 9 | check SKILL + flow + workflow + best-practices + scenarios 反复 |
| 读后写硬门 / 写前硬门 | 8 | exec SKILL + carrier-rules + workflow + best-practices + scenarios |
| 完成判定 / 未 archive = 未完成 | 7 | flow / scope-boundary / finish / workflow / glossary / best-practices |
| 作用域边界 / ≤20 行豁免 | 7 | flow + scope-boundary + user-prompt(脚本) + getting-started + best-practices + scenarios |
| design.md 写入界限 | 4 | flow / check / workflow / plan |

**问题**: 这些是**机器不变量** (单一定义即可), 却散落成"每文件各写一段"。任一约束变更需改 7-19 处, 必漂移。例: `skein-executor` 在 reference.md 说 model 继承主模型, 在 glossary 说 `model: sonnet + effort: medium` (skein-executor.md 实际无 model 字段 = 继承), 说法已不一致。

**优化方向 [可破坏性]**: 抽一层 `core-契约` 单一真值源 (类似 Trellis 的 spec/invariants), 各 skill/agent/docs 只**引用** ("见 core 契约 §X") 不复述。最有价值合并: dispatch 6 字段模板 (现散在 carrier-rules + scheduling-algorithm + 6 个 agent 各写) → 一处定义, agent 只写"遵循 dispatch 标准模板"。

**预估收益**: 命中文件数砍 50%+, 单约束维护一处; 规则漂移根除。每加载一个 skill 省 ~200-400 token (去重措辞)。

---

## 2. SKILL.md 体积 (skill 注入占 context)

每个 SKILL.md 行数:

| skill | 行 | 评估 |
|---|---|---|
| skein-memory | 80 | 偏长 (含 recall/sediment/bootstrap/reconstruct 四职责) |
| skein-plan | 80 | 偏长 |
| skein-clean | 65 | 含两清扫项明细, 可下沉 references |
| skein-exec | 70 | 调度门本体 + 反例长 |
| skein-setup | 70 | 初始化+维护+迁移分流 |
| skein-grill | 59 | OK |
| skein-flow | 53 | OK (多为委托指针) |
| skein-research | 51 | OK |
| skein-check | 49 | OK |
| skein-finish | 43 | 最精简 |

**description (frontmatter, 模型决策加载时恒注入) 总量**: 10 个 skill description 合计 2243 字符 ≈ **560 token**。最长 skein-exec (342 字符) / skein-check (249) / skein-memory (265)。

**问题**: SKILL.md 正文按"渐进式披露"设计 (references 存明细), 但仍有 **正文重复 references 内容** 的情况:
- skein-memory SKILL 70 行里 reconstruct 三档表 (recall/full/deep) 与 `references/reconstruct-memory.md` (189 行/17.2K) 重复, 正文表可缩为指针。
- skein-exec SKILL 反例段 (行 70) 与 scheduling-algorithm.md 反例重叠。

**优化方向 [可破坏性]**: SKILL.md 收敛到 ≤50 行纯路由 + 触发条件, 明细全下沉 references。skein-memory 把 reconstruct/bootstrap 两节 (占 ~30 行) 各压成 1 行指针。skein-exec 调度门正文与 references 合并去重。

**预估收益**: 每个 SKILL.md 砍 15-30 行, 模型主动加载 skill 时省 100-300 token/次; 正文/refs 不再双份维护。

---

## 3. agent.md 体积

| agent | 行 | tools | 绑定 skill |
|---|---|---|---|
| skein-setup | 53 | RW+Bash+检索 | skein-setup |
| skein-researcher | 74 | R+检索+Bash+Web | skein-research |
| skein-memorier | 43 | R+Bash+检索 | skein-memory |
| skein-dedup | 49 | R+Bash+检索 | **无** |
| skein-finisher | 41 | R+Bash+检索 | skein-finish |
| skein-executor | 37 | RW+Bash+检索 | **无** |
| skein-checker | 37 | R+Bash+检索 | skein-check |

**问题**:
- 每个 agent 的"铁律"段重复 Recursion Guard / 不与用户对话 / 缺信息标 `需要:` —— **6 个 agent 各写一遍同三条** (~每 agent 4-6 行 = 共 ~30 行纯重复)。
- skein-researcher.md 74 行最长, 其"结论落盘"段 (15 行) 与 skein-research skill 的"落盘"段、skein-memory bootstrap-seeding 的落盘格式**三处重复**。
- skein-setup.md 53 行, 迁移流程 5 步与 setup SKILL + trellis-migration.md 内容高度重叠。

**优化方向 [可破坏性]**: 抽公共 agent 铁律 (Recursion Guard / 无 AskUserQuestion / `需要:` 协议 / 读后写硬门) 到一处 (plugin 级 agent 约定或 SKILL 内), 各 agent.md 只写**本 agent 独有职责 + 输入 + 输出格式**。预期每 agent 砍 8-12 行。

**预估收益**: 6 agent 共省 ~60 行; agent 派发时注入的 system prompt 减重。

---

## 4. docs 重复

docs/ 7 篇 + README + docs/examples/README:

| 文档 | 行 | 重复点 |
|---|---|---|
| reference.md | 185 | 速查 CLI/skill/agent/hook/config — 与 SKILL.md description + agent.md 职责段**整片重复** |
| workflow.md | 188 | 运行机制 — 角色/闭环/调度/记忆/护栏, 与各 SKILL 正文 + glossary 大面积重叠 |
| best-practices.md | 138 | 决策流程图 + 反例黑名单 — 反例与 flow/exec/check 各 SKILL 的反例段重复 |
| scenarios.md | 129 | 9 场景 — 与 getting-started + scope-boundary 重复 (场景 6 与作用域边界表同) |
| glossary.md | 75 | 术语 — **相对独立有价值**, 是唯一不与 SKILL 重复的篇 |
| getting-started.md | 94 | 与 README + docs/README "一句话上手" + 作用域边界表重复 |
| docs/README.md | 49 | 索引 — OK, 但"核心概念速览"与 glossary 重复 |

**问题**: docs 是**给人读**的 (模型日常不加载), 但内容 = 各 SKILL 正文的人工重述版。模型走 skill 闭环时 docs 不进 context, 所以 docs 重复**不直接烧 token**, 但**维护成本高**: 同一概念 (闭环/sediment/调度) 在 skill + docs 各维护一份, 漂移必然。例: reference.md 说 skein-checker `model: haiku + effort: medium`, 但 skein-checker.md frontmatter 写 `model: haiku` 无 effort 字段 → 实际行为取决于代码, 文档已对不上。

**优化方向 [可破坏性, 但低优先 — docs 不进 context]**: docs 收敛为 **glossary (术语) + getting-started (上手) + reference (速查, 纯指针指向 skill)** 三篇, 删 workflow.md/best-practices.md/scenarios.md (其内容已在 skill + references)。或保留但加"权威源 = SKILL.md, 本文为导读"头注, 改动时只改 SKILL。

**预估收益**: docs token 不省 (不进 context), 但维护面砍 50%, 文档与 skill 漂移减少。

---

## 5. skein.py 体积与结构 (2764 行, god-object)

单 `Skein` 类 **88 个方法** (grep `^    def`), 跨 9 个不相关职责域:

| 行段 | 方法群 | 职责域 |
|---|---|---|
| 175-410 | __init__/config/_load/_save/_all/_render_tasks/_scaffold | **持久化 + 状态机核心** |
| 422-892 | create/start/finish/archive/del_/clean/current/ready/pop/status/list_/contract | **task 生命周期 CLI** |
| 893-1210 | doctor/_quality_gate/session_context/user_prompt/_classify_prompt | **doctor + hook 注入** |
| 1211-1494 | board/_board/_write_if_changed/_board_task | **看板渲染** |
| 1495-1987 | _board_data/_dashboard/_queue/_search/_board_html/_webapp_html/_exec_argv | **看板数据 API (JSON)** |
| 1988-2626 | view/serve/_run_server/_build_serve_app/_serve_app_factory | **HTTP 服务器 (fastapi/uvicorn)** |
| 2365-2564 | _migrate_trellis_tasks/_purge_wiring/_purge_trellis_hooks/_disable_trellisx_plugin/setup | **trellis 迁移** |

**问题 (god-object)**: 一个类同时是 ① 任务状态机 ② CLI 入口 ③ hook 注入器 ④ 看板渲染器 ⑤ HTTP 服务器 ⑥ trellis 迁移器。`_build_serve_app` 单方法 ~230 行 (2134-2364), `_render_tasks`/`_board_data` 各 200 行。HTTP 服务器 (fastapi/uvicorn 依赖) 占 ~640 行 (1988-2626) 却只在 `web_serve=true` 时用, 是**可选重依赖**与核心耦合在一起。

**优化方向 [可破坏性, 中风险]**:
- 拆分: `skein.py` 核心 (状态机 + CLI + hook) 留 ~1500 行; 看板渲染/HTTP 服务抽 `board.py`/`serve.py`; trellis 迁移抽 `migrate.py`。
- HTTP 服务 (fastapi/uvicorn) 是**纯可选** (web_serve=false 时 no-op), 抽独立模块 + 惰性 import, 核心零重依赖。
- `_classify_prompt` (启发式 3 档) 与 `_render_tasks` 等大方法可独立函数化。

**注意**: 拆分是破坏性重构, 需跑 `test_skein.py` (381 行) + `test_board.py` (273) + `test_statemachine.py` (192) + `test_dag.py` (217) 全绿兜底。当前测试覆盖存在, 风险可控。

**预估收益**: 单文件可读性 + 可维护性大幅提升; 核心引擎与可选 HTTP 解耦 (不用看板的仓零依赖)。token 无直接收益 (脚本不进 context), 但后续改 bug / 加功能成本骤降。

---

## 6. 跨 skill 一致性 (10 skill 间概念重复 / 术语漂移)

术语 / 概念在多 skill 定义, 已观测到不一致:

| 概念 | 不一致点 |
|---|---|
| 执行 agent 默认 | skein-executor.md 无 model 字段 (继承主); reference.md 说 "默认继承主模型高推理"; glossary.md 说 skein-checker `model: sonnet + effort: medium` (但 checker.md 实为 `haiku`)。**三处说法两两矛盾** |
| 6 字段 vs 5 字段 | 全局 CLAUDE.md 用"五要素"; skein 用"6 字段 dispatch prompt"。两套术语并存, 未统一 |
| "执行 agent 由 main 选现有 agent (无则 general-purpose)" | skein-executor.md / reference.md / README.md 说 "无则 skein-executor"; 但 docs/README 第 24 行 + best-practices 仍残留 "无则 general-purpose"。**general-purpose 已被 skein-executor 取代, 文档未全清** |
| 完成 = 未 archive | 措辞 7 种变体 ("未 archive = 未完成" / "未 archive = 未闭环" / "禁宣告 Done" / "闭环不可跳步") |
| subtask 自愈 | skein-exec SKILL 说 "≤2 轮原地重派"; scenarios.md 说 "≤2 轮"; scheduling-algorithm.md 说 "≤2 轮"。一致但分散 |

**优化方向 [可破坏性]**: 建术语表 (glossary 已有雏形) 作单一真值源, 各 skill 用同一术语。清 general-purpose 残留 (统一 skein-executor)。统一 5 要素/6 字段措辞。

**预估收益**: 消除矛盾描述 (模型不再被两版说法搞混); 维护单点。

---

## 7. 死代码 / 悬挂

| 项 | 状态 | 证据 |
|---|---|---|
| **agents/skein-dedup.md** | **悬挂** — 磁盘有文件, **未在 plugin.json `agents` 注册** (只注册 6 个, dedup 是第 7 个), 故 Claude Code 不识别为可用 agent | plugin.json agents 列表 6 项无 dedup; 仅 skein-plan SKILL 行 63/80 文字引用它 |
| skein-plan SKILL 引用 dedup | plan SKILL 写 "异步派 skein-dedup", 但该 agent 未注册 → **派发会失败/落到 general-purpose** | 同上 |
| 其他 agent/skill/doc | 均有引用, 无死文件 | grep 交叉验证 |

**优化方向 [可破坏性]**: 二选一 — ① 把 skein-dedup 注册进 plugin.json agents (若要保留查重能力); ② 删 agents/skein-dedup.md + 清 plan SKILL 的引用 (若查重并入 plan 主流程)。当前是"半死"状态最糟。

**预估收益**: 消除"派了不存在的 agent"的隐性故障; 减一份 49 行悬挂 agent.md。

---

## 8. hook 注入开销

hook 注入点 + 预算 (plugin.json + memory.py + skein.py):

| hook | 注入内容 | 预算 | 频率 |
|---|---|---|---|
| SessionStart | ① `skein-memory session-start` core **极简索引** (每条 1 行标题) | INDEX_BUDGET_TOKENS=400 | 每 session 1 次 |
| SessionStart | ② `skein session-context` 活跃 task 恢复 | SESSION_CTX_BUDGET_TOKENS | 每 session 1 次 |
| UserPromptSubmit | `skein user-prompt` task 判定提醒 (固定 ~15 行) | SESSION_CTX_BUDGET_TOKENS | **每 prompt (最高频)** |
| SubagentStart | `skein-memory subagent-start` core **全文** + spec 纪律 head | SUBAGENT_BUDGET_TOKENS=2000 | 每 subagent 派发 |
| PreToolUse | guard (无注入, 仅 block) | 0 | 每 Edit/Write/Read |
| PostToolUse | fmt + spec-meta (warning 才注入) | 0-小 | 每写盘 |
| PermissionRequest | allow (无注入) | 0 | 每授权 |

**预算守卫**: `hooklib.budget_guard` 硬截断 (CHARS_PER_TOKEN=4), 注入超预算 stderr 告警 + 截断。设计合理。

**问题**:
- **UserPromptSubmit 每 prompt 必注入** 是最大开销点: 固定注入 task 判定模板 (~15 行, 行 1198-1206), 含 3 档启发式结果 + "MUST 输出判定行" + flow 指引 + 查重句。每 prompt ≈ 300-400 token, 长会话累计显著。且注入的 `_classify_prompt` 启发式 (skein.py 1144-1182) 命中率有限 (中文动词/名词关键词表硬编码), 多数 prompt 落 "模糊" 档 → 启发式价值存疑。
- **SubagentStart 注入 core 全文** (≤2000 token): 每派一个 subagent 都注入整份 core 规则。core 规则少时 OK, 多时 (CORE_BUDGET=8000 字符) 每 subagent 重复烧 2000 token。subagent 是短命执行体, 全量 core 是否都需要存疑 (执行单个 subtask 可能只相关 1-2 条 core)。
- SessionStart 双注入 (memory session-start + skein session-context) 合理, 预算小。

**优化方向 [可破坏性]**:
- UserPromptSubmit: 已初始化的仓, task 判定模板可**只在 model 实际有歧义时**注入 (或缩到 3 行: "复杂请求→skein-flow; 简单→直接做; 不确定→AskUserQuestion")。`_classify_prompt` 启发式可砍 (价值/复杂度比低), 让 model 直接判。
- SubagentStart: 改注入 core **索引** (同 SessionStart 极简版) + 按需 inject-core, 而非全文。subtask 调度时 dispatch prompt 已带相关 core 条目 (planning recall 注入), 全量 core 重复。

**预估收益**: UserPromptSubmit 每省 200 token × 长 session 数百 prompt = 显著; SubagentStart 索引化每 subagent 省 ~1500 token。

---

## 总结: 优化优先级 (按收益/成本)

| 优先级 | 项 | 收益 | 成本 |
|---|---|---|---|
| P0 | 修 skein-dedup 悬挂 (注册或删) | 消除隐性故障 | 极低 |
| P0 | 抽 dispatch 6 字段 + agent 公共铁律单一真值源 | 去 19+14 处重复 | 中 (破坏性) |
| P1 | UserPromptSubmit 注入瘦身 + 砍 _classify_prompt | 每 prompt 省 token | 低 |
| P1 | SubagentStart core 索引化 (非全文) | 每 subagent 省 ~1500 token | 低 |
| P1 | 清 general-purpose 残留 + 术语统一 (skein-executor) | 消矛盾 | 低 |
| P2 | SKILL.md 正文下沉 references (memory/exec 优先) | 加载省 token | 中 |
| P2 | skein.py god-object 拆分 (serve/board/migrate 独立) | 可维护性 | 高 (破坏性, 有测试兜底) |
| P3 | docs 收敛 (删 workflow/best-practices/scenarios 重述) | 维护成本 (不省 token) | 中 |

**整体判断**: SKEIN 设计成熟 (双层记忆 / 双层 DAG / hook 护栏 / 渐进式披露都对), 但**经历了多次增量演进** (trellis 迁移 / 看板 HTTP 服务 / reconstruct / bootstrap / dedup), 增量未充分收敛 → 表现为 ① 概念多处重述 ② god-object ③ 半死文件 ④ 注入过重。学 Trellis 优化的核心抓手 = **抽单一真值源层** (dispatch 模板 / agent 铁律 / 术语) + **拆 skein.py** + **hook 注入瘦身**。
