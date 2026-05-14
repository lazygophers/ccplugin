# cortex playbook 借鉴 — SKILL 拆 references + digest 加经验抽取

## Goal

借鉴 zhaono1/agent-playbook 两条方法论提升 cortex 长期可维护性:
1. **Context layering Layer 3** (planning-with-files / context-layering 文档): SKILL.md 留 procedural, 详细规范挪 `references/*.md`, 减启动加载成本
2. **Self-improving-agent 多 memory + 反馈循环**: cortex 现有 episodic (sessions/jsonl) + working (hot.md), **缺 semantic (patterns 库)**。融入 cortex-digest 第 5 类抽取, 扫 sessions/ jsonl → 抽复发 pattern → 写 patterns 库 → 阈值过线时提议 patch SKILL/AGENT (走 cortex-refactor 用户确认)

## What I already know

- `cortex-ingest/SKILL.md` 497 行 / 27.5KB, §1-§9 全部细则混在单文件
- `cortex-digest/SKILL.md` 175 行 / 9.8KB, 已有五阶段 (读/析/处/更新/清理) + 反思·连接·矛盾·决策 4 类抽取
- cortex 现有 memory 三层:
  - episodic: `记忆/L4-流水账/sessions/<cli>/<YYYY>/<MM>/<DD>/*.jsonl` (Stop hook 自动落)
  - working: `记忆/working/hot.md`
  - **semantic 缺**: 没有从 episode 抽取的可复用 pattern 库
- cortex-refactor 3 子操作 (rename/merge/split), 走 AskUserQuestion 用户确认
- AGENT.md §协作约定 3 = vault 写硬契约 (L1 MCP / L2 obsidian CLI / L3 直接 IO)
- cortex 21 skill, 自动 10 / 显式 11; cortex-digest 是自动 skill
- 路径硬编码 `$HOME/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex`

## Decision (ADR-lite)

**Context**: 4 个关键设计点经 AskUserQuestion 用户确认 (2026-05-14)

**Decision**:
- D1 — patterns 库位置/格式: `记忆/L0-核心/patterns.md` 单 markdown 文件, 多 section 按 category 组织。**Why**: vault md-native 约定, 与 hot.md 同 L0 层 (semantic 一等公民), 单文件检索成本低于多文件目录。
- D2 — 反写执行模式: proposal 文件 + cortex-refactor AskUserQuestion 单次确认 → 直接 patch SKILL/AGENT。**Why**: cortex-refactor 已建立用户确认 + 落盘的模式, 不走 git PR 减一层流程; AskUserQuestion 弹窗内"接受"等同授权 patch。
- D3 — 抽取触发: 内联 cortex-digest 每次跑 (digest 已是 daily cron), 不新增 cron。**Why**: digest 本身是 daily 抽取 skill, evolution 是其第 5 类抽取维度, 复用调度无 overhead。
- D4 — 阈值: 硬编码 `confidence ≥ 0.8 AND applications ≥ 3`, 不暴露配置。**Why**: 实现简单, 后续调整走代码改; 不增加 _meta/version.json 字段膨胀。

**Consequences**:
- D2 反写直接 patch 风险: 用户点"接受"后 SKILL.md 立即变 = 必须 git working tree clean 才允许 patch, dirty 则拒并提示 commit (新增安全门)
- D4 硬编码: 后续若想调阈值需改 scripts/cli/digest.py 重发布

**SKILL.md 拆分硬上限**: ~200 行 procedural, 超出挪 references/。

## Requirements (evolving)

### R1: cortex-ingest SKILL.md 拆 references/ (P0-1)

- SKILL.md 保留 §调用优先级 + §触发场景 + §输入信号 + §流程 (主) + §错误处理 + §AUTO_MODE, 控制 ≤ 200 行
- 详细规范拆 4 个 references:
  - `references/layout.md` — §1.1 4 层目录 + §5 分级评分 + §1.2 拒交条件
  - `references/extract.md` — §3 frontmatter + §4 深度处理 + §4.7 覆盖度自检 + §7 6 类抽取
  - `references/exclude.md` — §8 强制排除清单
  - `references/knowledge-graph.md` — §9 Bases/Canvas/Wikilink/websearch 4 制品
- SKILL.md 主流程节点点引 `详见 references/<name>.md §X`
- §6 tag 强制约定保留 SKILL (短, 高频参考)
- §2 嵌套 repo / §3 frontmatter schema 保留 SKILL (短, 高频参考)

### R2: cortex-digest SKILL.md 也拆 references/

- 175 行 + 加 evolution 抽取后会膨胀 ~300 行, 提前拆
- SKILL.md 留五阶段骨架 + 调度 + AUTO_MODE
- references:
  - `references/extraction.md` — 4 类 (反思/连接/矛盾/决策) + 路由表 + 6 信号识别
  - `references/evolution.md` — 新增第 5 类 (经验抽取) + patterns schema + 反写流程
  - `references/cleanup.md` — §5 清理 ≥30 天复扫

### R3: cortex-digest 加第 5 类抽取 (经验 / Evolution, P1-4 融入)

`evolution` 维度, 与现有 4 类 (反思/连接/矛盾/决策) 并列:

#### 3.1 输入源
- `记忆/L4-流水账/sessions/<cli>/<YYYY>/<MM>/` 月度 jsonl
- 默认扫上 7 天 (digest daily 调度) — 配 frontmatter `digest.evolution_lookback_days: 7` 可调

#### 3.2 抽取规则
- 复发模式: 同 skill 在 N 个 session 中遇相同失败 / 同问题重复出现 / 同决策反复走
- 阈值: `applications ≥ 3` (出现 ≥ 3 次) 才入 pattern 候选
- 用户反馈信号: jsonl 内用户消息含纠正语 ("不对" / "不是" / "应该是" / "改成") → 标记为 high-confidence 失败 pattern

#### 3.3 落盘
- `记忆/L0-核心/patterns.md` — semantic 汇总, 单文件多 section (按 category)
- 每 pattern 含: `id` / `name` / `category` / `source` (episodic ref) / `confidence` / `applications` / `created` / `pattern` / `problem` / `solution` / `target_skills`
- 格式 markdown table 或 section, 不用 JSON (vault md-native)

#### 3.4 反写提议 (skill/agent patch)
- 阈值 (硬编码 D4): `confidence ≥ 0.8 AND applications ≥ 3` → 入提议队列
- 生 `_assets/evolution-proposals/<YYYY-MM-DD>-<slug>.md` 提议文件:
  - 目标 skill/agent 路径
  - 建议 patch (unified diff 形式)
  - 来源 pattern id + episodic refs
- digest 输出 evolution_proposals 列表, **下次 cortex-digest 跑或用户主动调 cortex-refactor 时**通过 AskUserQuestion 单次确认 → 立即 patch SKILL/AGENT 源文件 (D2 模式)

#### 3.5 安全门
- 反写仅限 SKILL.md / AGENT.md / agent .md, **禁** patch python / bash 代码 / commands/*.md (用户 facing)
- patch 前必须 git working tree clean (针对插件目录 plugins/tools/cortex/), dirty 则拒绝并提示用户先 commit (D2 consequence)
- AskUserQuestion 弹窗内用户未点"接受"前, proposal 文件不动 SKILL 内容

### R4: lint / 文档 / 测试

- lint 加规则 19 `skill-references-exists` — SKILL.md 引用 `references/<name>.md` 必须文件存在 (autofix=false, warn 级)
- docs 同步: `docs/Skills 详解.md` 加 references/ 章节 + evolution 抽取说明
- 测试:
  - `tests/python/test_digest_evolution.py` — mock sessions/ jsonl, 验证抽取 + 提议生成 + 阈值过滤 (硬编码 0.8 / 3 边界值)
  - `tests/python/test_skill_references_lint.py` — SKILL 引用不存在 references → warn
  - `tests/python/test_evolution_safety_gate.py` — git dirty 拒 patch, 仅 SKILL/AGENT 白名单

## Acceptance Criteria (evolving)

- [ ] cortex-ingest SKILL.md ≤ 200 行, 4 个 references/*.md 落地
- [ ] cortex-digest SKILL.md ≤ 200 行, 3 个 references/*.md 落地
- [ ] cortex-digest 加第 5 类 `evolution` 抽取, scripts/cli/digest.py 实现 sessions/ jsonl 扫描 + pattern 候选生成
- [ ] `记忆/L0-核心/patterns.md` schema 定义 + 首次生成 stub
- [ ] proposal 文件生成路径 `_assets/evolution-proposals/<YYYY-MM-DD>-<slug>.md` 验证
- [ ] lint rule 19 实现 + 测试通过
- [ ] 测试基线 324 → 至少 +5 (新增 evolution + references 测试)
- [ ] 文档同步 `docs/Skills 详解.md` + `.claude/memory/cortex-plugin-2026-05-13.md`

## Definition of Done

- pytest 全绿
- ruff check + format 通过
- 任何 SKILL.md 修改后跑 `claude --settings ~/.claude/settings.glm-4.7-flash.json -p "<待测>"` 验证 AI 理解 (CLAUDE.md §代码质量检查规范)
- cortex-digest --dry-run 在真实 vault (`/Users/luoxin/persons/knowledge/obsidian`) 跑一遍验证抽取行为
- 文档 / memory 索引同步

## Out of Scope (explicit)

- 不做 P0-2 (cortex-ingest `_ingest_state.md` 长任务恢复) — 用户明确"其余不动"
- 不做 P1-3 (声明式 hook frontmatter / cortex-orchestrator) — 用户明确"其余不动"
- 不做 P2 (agent state file / cortex-router) — 用户明确"其余不动"
- 不改 vault.lang / preset / hook bash 脚本 / cron 调度
- 不破坏现有 cortex-digest 4 类抽取 — evolution 是第 5 类**新增**, 不替换
- 不直接修改 SKILL/AGENT 源文件 (反写走 proposal 文件 + 用户确认)

## Technical Notes

- agent-playbook 参考: [`research/playbook-methodology.md`](research/playbook-methodology.md)
- cortex 当前真相: `.claude/memory/cortex-plugin-2026-05-13.md`
- cortex-ingest §1-§9 全细则: `plugins/tools/cortex/skills/cortex-ingest/SKILL.md`
- cortex-digest 五阶段: `plugins/tools/cortex/skills/cortex-digest/SKILL.md`
- cortex 写契约 (MCP 强制): `plugins/tools/cortex/AGENT.md §协作约定 3`
- lint 规则定义: `plugins/tools/cortex/scripts/lint/rules.json`

## Research References

- [`research/playbook-methodology.md`](research/playbook-methodology.md) — agent-playbook 8 核心方法论摘要 + 借鉴映射 (待 sub-agent 写)
