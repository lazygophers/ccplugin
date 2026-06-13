# cortex skills/agents 整改 — 删 6 合 1 拆 6 + agent 边界澄清

## Goal

cortex 当前 21 skill + 7 agent 存在大量功能交叉、违反 Claude Code 官方 skill 渐进披露规范 (单文件 SKILL.md 过长)、skill 与 agent 边界模糊。本任务整改至 14 skill / 5-6 agent, 全部多文件 + references/ 渐进披露 + 单一职责 + agent 边界明确。

## What I already know

### 现状 (审计)

**21 skill 多文件度量** (合规 3, 违规 18):

- ✅ 多文件渐进披露: cortex-ingest (5 文件), cortex-digest (4), cortex-memory (2)
- ❌ 单文件超 200 行 (必拆): cortex-dashboard (320), cortex-install (320), cortex-save (219), cortex-lint (204)
- ❌ 单文件超 150 行 (建议拆): cortex-search (178), cortex-refactor (174)
- ❌ 功能交叉应删/合: cortex-new (73), cortex-canvas (73), cortex-reflect (67), cortex-forget (65), cortex-ingest-bulk (52), cortex-schema (52), cortex-locale (51)
- ❌ 单文件应合: cortex-recall (88) → cortex-search

**7 agent**: cortex-archivist / cartographer / curator / linker / researcher / summarizer / translator
- 与 skill 重叠: linker ↔ recall (建议删 linker)
- 边界不清: archivist↔refactor, curator↔lint, cartographer↔dashboard, summarizer↔digest, researcher↔ingest, translator↔locale (建议加分工注释)

### 关联资产

- **20 slash commands** (`commands/*.md`): 6 删 skill 全无对应 slash, 6 删整改无 slash 副作用
- **24 bash wrappers** (`scripts/*.sh`): 6 删 skill 全无对应 wrapper, 整改无 bash 副作用
- **合并/拆分仍需更新**: docs/Skills 详解.md, docs/Agents.md, docs/索引.md, AGENT.md, .claude/memory/cortex-plugin-2026-05-13.md, .claude/rules/MEMORY.md, README/CHANGELOG

## Requirements

### MVP

1. **删 7 skill**: cortex-new, cortex-canvas, cortex-reflect, cortex-forget, cortex-ingest-bulk, cortex-schema, cortex-locale (forget skill 删, slash + wrapper 保 → AI 加载 memory skill)
2. **合 1 skill**: cortex-recall → cortex-search/references/memory-recall.md
3. **拆 6 大 skill 到 references/** (SKILL.md 入口 ≤ 80 行 + references/<topic>.md):
   - cortex-dashboard (320 → 80 + 3-4 子文件)
   - cortex-install (320 → 80 + 4 子文件 install/update/cron/config)
   - cortex-save (219 → 80 + 2-3 子文件)
   - cortex-lint (204 → 80 + 2 子文件: rules + autofix)
   - cortex-search (178 → 80 + 2 子文件: mcp-tiers + recall)
   - cortex-refactor (174 → 80 + 2 子文件: rename-merge + split)
4. **agent 整改**:
   - 删 cortex-linker (功能并入 cortex-search/references/memory-recall.md)
   - 每个保留 agent 头部加 "vs <skill>" 分工注释行
5. **同步更新文档**: docs/* / AGENT.md / .claude/memory/cortex-plugin-2026-05-13.md / .claude/rules/MEMORY.md / 资产计数
6. **同步 bash**: 6 删 skill 无 wrapper 影响, 但需扫 `scripts/install_wrappers.sh` 是否引用废 skill 名 (KEEP_LIST 已含合法 24 个, 无残留风险)
7. **回归验证**: 跑 `claude -p "<待测>"` 对每个保留 skill 的 SKILL.md 入口验 AI 识别正确

## Acceptance Criteria

- [ ] Skill 数 21 → 13 (删 7 + 合 1)
- [ ] 全部 13 skill 含 references/ 子目录 (至少 1 个子文件)
- [ ] 每个 SKILL.md 入口 ≤ 80 行 (含 frontmatter + 触发词 + 关键决策树 + AUTO_MODE 分支 + references 指针)
- [ ] 每个 SKILL.md 入口含 AUTO_MODE 分支处理 (D10): `auto` 入参时跳 AskUserQuestion 走默认值
- [ ] 全部 24 wrapper (`scripts/*.sh`) 调 `claude -p "/cortex:<name> auto"` (非 auto 模式 only 在交互会话)
- [ ] 任何 skill 不接收位置参数 (D9): grep SKILL.md 无 `ARGUMENTS: <var>` 或 `$1` 处理
- [ ] agent 数 7 → 6 (删 linker)
- [ ] 每个保留 agent 头部含 "vs <skill>" 分工边界注释
- [ ] docs/Skills 详解.md / Agents.md / 索引.md 计数表全部更新
- [ ] .claude/memory/cortex-plugin-2026-05-13.md 资产计数刷新
- [ ] 每个改动的 skill 跑过 `glm-4.7-flash` 识别测试, 返回非空
- [ ] `scripts/install_wrappers.sh KEEP_LIST` 不需改 (无新增/删除 wrapper)
- [ ] lint 全绿: `bash ~/.cortex/scripts/lint.sh --vault <test-vault>`

## Definition of Done

- 测试: glm-4.7-flash 对每个改动 skill 入口验 AI 识别 (返回非空)
- Lint: ruff check 通过
- 文档同步: 计数表 / 记忆 memo / MEMORY.md 全部刷新
- Rollback 可行: 删的 skill 在 PR1 单独提交便于 revert
- bash wrapper 无变动 (确认), 否则需补 install_wrappers.sh

## Out of Scope

- 不动 20 slash commands (除非废 skill 对应 slash, 但审计确认 6 删 skill 无 slash)
- 不动 24 bash wrappers
- 不改 .claude-plugin/plugin.json hook 注册
- 不动 python CLI (`scripts/cli/*.py`)
- 不改 cron 任务
- 不重写 cortex-ingest/cortex-digest/cortex-memory (已合规)
- 不删 cortex-forget (除非用户明示, 它有 slash + wrapper)
- desktop 项目 memo 精简 (out-of-scope)

## Technical Approach

**4 PR 分批**:

| PR | 内容 | 风险 |
|---|---|---|
| PR1 | 删 6 skill (canvas/new/reflect/ingest-bulk/schema/locale) + 合 recall→search | 低 (废 skill 无 slash/wrapper, 易 revert) |
| PR2 | 拆 4 大 skill (dashboard/install/save/lint) 到 references/ | 中 (改 SKILL.md 入口, 需 glm-flash 回归) |
| PR3 | 拆 2 中 skill (search/refactor) 到 references/ | 中 |
| PR4 | agent 整改 (删 linker + 5/6 agent 头部分工注释) + 文档计数同步 | 低 |

每 PR 自包含 + 测试 + 文档同步。PR1 是最干净的, 优先验证流程。

## Decision (ADR-lite)

**Context**: 21 skill 中 18 个违反渐进披露, 大量功能交叉, agent/skill 边界模糊。Claude Code 官方建议 SKILL.md ≤ 200 行 + references/ 按需加载, 否则启动每次塞满 prompt 高 token 成本。

**Decision**: 删 6 合 1 拆 6 → 14 skill, 全部多文件; 删 1 agent + 5 头部注释 → 6 agent 边界明确。

**Consequences**:
- ✅ 启动 prompt 体积下降 (每个 SKILL.md 入口 ≤ 80 行)
- ✅ Skill 触达精准 (description 含触发词)
- ✅ skill ↔ agent 分工写在文件里, 后续无需口口相传
- ⚠️ 4 PR 周期长, 文档同步多, 易遗漏一处计数
- ⚠️ 用户已有的 muscle memory 调 `/cortex:locale` 之类不存在, 不过审计确认无 slash, 影响零

## Resolved Decisions (用户授权"按最正确设计")

- **D1 cortex-forget**: 删 skill, 保留 `/cortex:forget` slash + forget.sh wrapper。slash 触发时 AI 加载 cortex-memory skill 走 forget 子流程 (slash 是命令快捷, skill 是知识+流程, 二者解耦)。
- **D2 SKILL.md 入口行数上限**: ≤ 80 行 (frontmatter ~10 + 触发说明 ~15 + 决策树/契约 ~35 + references 指针表 ~20)。
- **D3 references/ 子文件粒度**: 按职责粗拆 2-4 个子文件。每子文件单一主题 ≤ 250 行。过细 (5+) 割裂上下文。
- **D4 cortex-linker agent**: 直接删, 不留 deprecated 标记 (测试阶段无用户兼容性顾虑)。
- **D5 cortex-locale skill**: 直接删 (无 slash 无 wrapper, 配置归 cortex-doctor 或 cortex-install 配置子文件)。
- **D6 删 skill 全清单 (7 个)**: cortex-new, cortex-canvas, cortex-reflect, cortex-ingest-bulk, cortex-schema, cortex-locale, cortex-forget(skill 部分)。
- **D7 合并 skill (1 个)**: cortex-recall → cortex-search/references/memory-recall.md。
- **D8 最终数**: 21 → **13 skill** (21 - 7 删 - 1 合), 7 → **6 agent** (删 linker)。
- **D9 Skill 无参数契约**: 所有 skill 入口不接受位置参数。多分支决策时, skill 用 `AskUserQuestion` 引导用户选; 不在调用面暴露参数。
- **D10 CLI auto 模式契约**: bash wrapper / cron / CI 等非交互场景调用 slash 时必须传 `auto` 后缀 (`/cortex:<name> auto`), 触发 skill 进入 AUTO_MODE: 跳过 AskUserQuestion, 按推荐默认值自动决策。所有 wrapper (`scripts/*.sh`) 调 `claude -p "/cortex:<name> auto"` 而非 `/cortex:<name>`。SKILL.md 入口必含 AUTO_MODE 分支处理决策树 (含在 ≤80 行内)。

## Technical Notes

- 审计度量来自 `wc -l skills/*/SKILL.md` + `find skills/<name>/ -type f | wc -l`
- 6 删 skill 对照: `commands/` 无对应 + `~/.cortex/scripts/*.sh` 无对应 → 整改无 slash/bash 副作用
- 文档关联点: docs/Skills 详解.md, docs/Agents.md, docs/索引.md (计数表), AGENT.md (§1 搜索契约提到 recall), .claude/memory/cortex-plugin-2026-05-13.md (资产计数), README/CHANGELOG
- 回归命令: `claude -p "<待测>" --output-format stream-json | jq -r 'select(.type == "result" and .subtype == "success") | .result'`
