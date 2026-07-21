# C 方向 a+b+c 组合方案落地深挖 (skein v2)

token 估算 = 字符数 // 4 (与 hooklib.CHARS_PER_TOKEN=4 一致)。所有数字 `python3` 实测。

## 关键解锁: SubagentStart stdin 已含 agent_type (实证)

Claude Code 官方 Hooks reference (https://code.claude.com/docs/en/hooks) 明示:
- SubagentStart hook stdin payload = `{session_id, agent_id, agent_type, ...}`
- **`agent_type` 即 agent 名** (matcher 过滤的就是它), 如 `skein-executor` / `skein-checker`
- 现状 `memory.py:129 subagent_start` 完全忽略 stdin (没读) — 故 a 方案「传类目 hint」**无需 main 注 env / 无需改 dispatch 链路 / 无需 prompt marker**, 直接在 hook 里读 stdin.agent_type 映射类目即可。

这消除了原勘察 hook-injection-trim.md 机会1(a)「需 main 派发时经环境变量/参数传类目 hint」的跨改动顾虑。

## 1. SubagentStart 注入新形态 (a+b 融合)

三种形态对比 (实测 token):

| 形态 | 内容 | chars | tok | vs 现状 |
|---|---|---|---|---|
| **现状** (memory.py:128-141) | head + core 全文 → budget_guard 截断 | 16472 → 截 8000 | 4118 → 截 2005 | 基线 (已病态截断, 半失效) |
| **形态 b (纯索引)** | 纪律 head(精简) + core 全量索引(类目+title) + recall 提示 | 508 | **127** | 省 ~1880 tok |
| **形态 a (类目过滤全文)** | head + 仅 hint 类目的 core 全文 | 5145-5726 | **1286-1431** | 省 ~570-720 tok |

**推荐融合形态 (a 为主 + b 兜底)**:
- hook 读 stdin.agent_type → 查 agent→类目映射表 → 注 **该类目的 core 全文** (形态 a, ~1300 tok)
- 末尾追加 **全量索引 + recall 提示** (~150 tok), 兜住「需类目外规则时跑 recall」
- 无 hint / 非 skein agent / 映射空 → fallback 注 **纯索引** (形态 b, 127 tok), 不注全文
- 总 token: 命中类目 ~1450 tok, 未命中 127 tok, 均远低于 SUBAGENT_BUDGET_TOKENS=2000, **不再触发截断**

head 精简版 (从 213→~180 chars): 删「命中 core 规则 (下列) 即硬约束」(类目过滤后该句已在 filtered body 里), 加 recall 引导句。

## 2. 类目 hint 传递机制 (file:line 落点)

**机制**: hook 读 stdin.agent_type, 硬编码 agent→类目映射 (dict)。零外部链路改动。
**落点**: `memory.py:129 subagent_start` 改 ~20 行:
1. 开头加 `payload = _read_hook_stdin()` (新 helper, ~6 行, 读 stdin JSON 取 agent_type, 容错返 None)
2. `AGENT_CATEGORIES = {"skein-executor": {...}, ...}` (映射表, ~8 行)
3. `cats = AGENT_CATEGORIES.get(agent_type)`; 命中 → 注该类目 body; 未命中/None → fallback 纯索引
4. 新增 `_core_text_by_cat(cats)` 方法 (从 _core_text 拆, ~5 行, 只取指定 parent.name 的规则)

**改动文件**: 仅 `memory.py` (1 个), ~30 行。**plugin.json / skein.py / dispatch 全不改**。
**fallback**: agent_type 非 skein-* / 映射为空 / stdin 读失败 → 注纯索引 (127 tok), 免污染其他插件 agent (现状 matcher 已放开到全 subagent)。

## 3. agent → 类目映射表 (7 agent)

依据各 agent frontmatter 职责关键词 (见证据) 判定其命中的 core 类目:

| agent (agent_type) | model | 职责核心 | 注入 core 类目 | 理由 |
|---|---|---|---|---|
| **skein-executor** | default | 写码/改配置/跑命令 | script, arch, git | 脚本规约 + 注解陷阱 + worktree 隔离 |
| **skein-checker** | haiku | 跑 lint/type/test + 契约核查 | script, arch | 脚本规约 + 注解陷阱 (pep563 易过 type-check) |
| **skein-researcher** | opus | 只读调研/选型/勘察 | script, arch, skill | 脚本规约 (纯 stdlib) + spec persist + skill 结构 |
| **skein-finisher** | haiku | 读 diff + 完成核对 | script, git | 脚本规约 + worktree (diff 在 worktree) |
| **skein-setup** | sonnet | 迁移 .trellis / 重组 spec | script, arch, skill, git, hook, command, plugin-arch, agent | 全量 (初始化涉及所有结构) |
| **skein-dedup** | haiku | 扫 task 查重 | (空 → fallback 索引) | 不碰代码, 只读 task.json, 无 core 规则命中 |
| **skein-memorier** | haiku | recall/sediment 草案 | (空 → fallback 索引) | 操作 spec 记忆本身, core 规则对它无约束意义 |

**注**: setup 是唯一需全量的 (迁移涉及所有结构), 但全量=16472 chars 会触发截断 — 故 setup 也走 fallback 索引 + 强 recall 提示 (它本就绑定 skein-memory skill, 会 recall)。
→ 实际: 6/7 agent 注类目全文 (~1300 tok), 1/7 (setup) + 2 个空映射走索引 (127 tok)。

## 4. core 降级清单 (c 治本)

逐条 core 规则判定 (body chars 实测):

| 标题 | 类目 | chars | 命中频次判定 | 建议 | 理由 |
|---|---|---|---|---|---|
| Agent 定义规范 | agent | 1881 | 长尾 (仅改 agent.md 时) | **降 recall** | 写 agent 时才用, 非 exec 常用 |
| skein agent 公共铁律 | agent | 1916 | **每次** (所有 skein agent 绑它) | **留 core** | Recursion Guard/无AskUser/需回传 — 每个 subagent 必读 |
| PEP 563 + FastAPI 注解陷阱 | arch | 1036 | 长尾 (仅写 FastAPI/pydantic 时) | **降 recall** | 触发场景窄 (Web 框架运行时类型内省) |
| spec 持久性陷阱 (worktree+gitignore) | arch | 875 | 中频 (写 spec/sediment 时) | **降 recall** | 仅 memorier/setup/finisher 命中 |
| Command 定义规范 | command | 774 | 长尾 (仅写 command 时) | **降 recall** | 写 command 时才用 |
| Git Worktree 隔离模式 | git | 1173 | **每次** (所有 subagent 在 worktree 内) | **留 core** | executor/finisher 必读的隔离边界 |
| Hook 链设计规范 | hook | 2347 | 长尾 (仅写 hook 时) | **降 recall** | 仅改 hook 时用, 且最长 (2347) |
| plugin.json 架构规范 | plugin-arch | 2660 | 长尾 (仅改 plugin.json 时) | **降 recall** | 仅 setup/改插件结构时用, 最长 |
| Python 脚本编写规约 | script | 1806 | **每次** (所有 subagent 碰 scripts/) | **留 core** | 纯 stdlib 硬约束, 高频 |
| Skill 多文件组织规范 | skill | 1752 | 长尾 (仅写 skill 时) | **降 recall** | 写 skill 时才用 |

**留 core (高频每次)**: 公共铁律(1916) + worktree(1173) + script(1806) = **4895 chars** ✅ < CORE_BUDGET 8000
**降 recall (长尾)**: 其余 7 条 = 11331 chars

降级后 core 总量 **4895 chars** (vs 现 16240), 回到预算内, `memory.py:99 _core_text` 告警消除。
注: 降级是 sediment 操作 (mv core/<cat>/ → recall/<cat>/ + reindex), 非代码改 — 但需经 skein-memory 判定门 (sediment SKILL 流程)。降级后留 core 的 3 条配合形态 a, subagent 注入更精准。

## 5. 改动文件清单 + 行数

| 文件 | 改动 | 行数 | subtask |
|---|---|---|---|
| `plugins/tools/skein/scripts/memory.py` | subagent_start 改: 读 stdin + 映射 + 类目过滤 + fallback 索引 + 新 helper/dict | ~30 行改 | ST-1 |
| `plugins/tools/skein/agents/*.md` (7 个) | dispatch prompt 加「需类目外规则跑 recall」提示 (可选, 兜底) | 每个 +1 行 | ST-2 (可选) |
| `.skein/spec/core/` → `recall/` | 7 条长尾降级 (sediment 操作) | 0 代码 (mv+reindex) | ST-3 |
| **合计** | | ~30 行代码 + 7 行 agent + spec 操作 | |

注: ST-1 单独即成形态 a+b 融合, ST-3 治本消除告警。ST-2 为软兜底 (形态 a 末尾已含 recall 提示, 可省)。

## 6. 风险与兜底

- **风险**: subagent 不 recall 则类目外规则丢 (原勘察机会1(b) 主风险)。
- **兜底 1 (形态 a 自带)**: 注的是「该类目全文」非「只索引」 — 命中类目的规则已在上下文, 无需 recall。recall 仅用于跨类目, 是增强非依赖。
- **兜底 2 (head 提示)**: head 末尾「需类目外规则跑 recall」+ 全量索引常驻, subagent 看得到有哪些规则可拉。
- **兜底 3 (agent.md)**: ST-2 在 dispatch prompt 明确「需 X 规则跑 memory.py recall X」。
- **残余风险**: setup 降为索引 (因全量超预算) — 但 setup 绑 skein-memory skill 本就会 recall, 可接受。
- **不变量守住**: core 常驻硬约束不变 (session_start 索引常驻 + inject-core 按需), subagent 改的是「全文注入」非「索引常驻」。

## 验收对照

- ✅ 注入新形态有 token 估算 (形态 b 127 / 形态 a 1286-1431 / 融合 ~1450, 对比现状截断 2005)
- ✅ 类目 hint 机制有 file:line 落点 (memory.py:129, 读 stdin.agent_type, 官方 schema 实证)
- ✅ core 降级清单逐条有判定 (10 条全覆盖, 留 core 4895 < 8000)
- ✅ agent → 类目映射 7 个全覆盖
- ✅ 改动行数有估算 (~30 行代码)

## 证据

- memory.py:33 CORE_BUDGET=8000; :35 SUBAGENT_BUDGET_TOKENS=2000; :96-103 _core_text 超预算告警; :110-115 _core_index; :118-126 session_start (注索引); :128-141 subagent_start (注全文+截断, **未读 stdin**); :144-158 recall
- hooklib.py:14 CHARS_PER_TOKEN=4; :80-92 budget_guard (硬截断)
- plugin.json: SubagentStart hook command=`skein-memory subagent-start`, matcher 放开到全 subagent (无 matcher 段)
- agent frontmatter: plugins/tools/skein/agents/skein-{checker,executor,researcher,finisher,setup,dedup,memorier}.md
- core 规则: .skein/spec/core/{agent,arch,command,git,hook,plugin-arch,script,skill}/*.md (10 条)
- Claude Code Hooks reference: https://code.claude.com/docs/en/hooks — SubagentStart stdin = {agent_id, agent_type, ...}, matcher 过滤 agent_type
