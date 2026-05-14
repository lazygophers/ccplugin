# cortex 修 wiki 残留 — 全部 wiki → 知识库 vault truth 对齐

## Goal

cortex 历史从 "wiki/" 顶层目录 vault 切换到 "知识库/" 4 子目录 (项目/领域/日记/收件箱) 后,
代码 + lint 描述 + docs + skill/agent 用户口令仍残留 "wiki" 字样, 导致用户看到误以为
"知识库放到了 wiki 目录下"。本任务批量替换 wiki → 知识库, 全栈一致性对齐。

vault 实际**无** wiki 目录, 此修复纯字符串/文档清理, 不动 vault 真路径。

## What I already know

### 残留位置 (grep 排除 wikilink/wikipedia 后)

#### 代码层 (3 处, 必改)

- `plugins/tools/cortex/scripts/cli/deep_search.py:84` — `_SCOPE_GLOB.get(scope, "wiki")` fallback (dead code, scope 332 已 validate)
- `plugins/tools/cortex/scripts/cli/deep_search.py:304` — 同上
- `plugins/tools/cortex/scripts/lint/rules.json:67` — rule 8 `index-missing-section` description "index.md 未包含某 wiki 顶级子目录"

#### docs 层 (4 文件, 5 处)

- `plugins/tools/cortex/docs/_internal/design-decisions.md:142` — "wiki 噪音" 历史叙事
- `plugins/tools/cortex/docs/快速上手.md:80` — 示例口令 "save this to wiki"
- `plugins/tools/cortex/docs/故障排查.md:135` — "wiki audit --fix" 示例命令
- `plugins/tools/cortex/docs/Lint 规则.md:21,81,182` — rule 8 描述 + 例子

#### skill / agent (2 处)

- `plugins/tools/cortex/AGENT.md:52` — "wiki audit / lint" 触发短语
- `plugins/tools/cortex/skills/cortex-lint/SKILL.md:13-14` — "wiki audit / 找 orphan" + "lint the wiki" 触发短语

### 不动 (排除)

- `wikilink` / `[[wikilink]]` — Obsidian 内部链接概念, 与 vault 目录无关
- `wikipedia` — 引用 wikipedia.org 外链
- `plugin.json:119` keywords `"wiki"` — marketplace metadata 描述 plugin 用途, 是英文通称, 不是路径

## Decision (ADR-lite)

**Context**: User AskUserQuestion 确认 "全部改 wiki → 知识库 (一致性)"

**Decision**: 
- 代码层 fallback `"wiki"` → `"知识库"` (与 SCOPE_GLOB["all"] = "知识库" 一致)
- rules.json + docs 中 "wiki 顶级子目录" / "wiki 噪音" → "知识库 顶级子目录" / "知识库 噪音"
- 用户口令短语 "wiki audit" / "save this to wiki" → "知识库 audit" / "save this to 知识库"
- AGENT.md + cortex-lint SKILL.md 触发短语对齐

**Consequences**:
- 用户原"wiki audit"口令不再生效 → 描述池语义匹配仍可能命中 (lint skill description 不只靠精确字面)
- 文档历史叙事改写, 但 git log 保留原文 (不破坏可追溯)
- 不动 plugin.json keywords (英文 marketplace 描述, 与路径无关)

## Requirements

### R1: 代码层替换

- `deep_search.py:84,304` — `"wiki"` → `"知识库"`
- `rules.json:67` — description "wiki 顶级子目录" → "知识库 顶级子目录"

### R2: docs 替换

- `docs/_internal/design-decisions.md:142` — "wiki 噪音" → "知识库 噪音"
- `docs/快速上手.md:80` — "save this to wiki" → "save this to 知识库"
- `docs/故障排查.md:135` — "wiki audit --fix" → "知识库 audit --fix"
- `docs/Lint 规则.md:21,81,182` — 3 处 "wiki 顶级子目录" / "wiki audit" → 对应中文

### R3: skill / agent 触发短语对齐

- `AGENT.md:52` — "wiki audit / lint" → "知识库 audit / lint"
- `skills/cortex-lint/SKILL.md:13-14` — "wiki audit / 找 orphan" → "知识库 audit / 找 orphan"; "lint the wiki" → "lint the 知识库"

### R4: 测试 + 验证

- 不破坏现有测试 (基线 360 不下降)
- `grep -rn 'wiki' plugins/tools/cortex/ | grep -vE 'wikilink|wikipedia|__pycache__'` 仅余 `plugin.json:119 "wiki" keyword` (marketplace metadata 保留)

## Acceptance Criteria

- [ ] 代码层 3 处全替换
- [ ] docs 5 处全替换 (4 文件)
- [ ] skill/agent 2 处全替换
- [ ] grep verify: 除 wikilink/wikipedia/plugin.json keyword 外 0 wiki 字符串
- [ ] pytest 全绿 (基线 360 不下降)
- [ ] ruff check 通过
- [ ] AI 质量检查 (CLAUDE.md §代码质量检查规范) 验证 cortex-lint SKILL 仍能识别

## Definition of Done

- pytest 全绿
- ruff check + format 通过
- AI 质量检查 cortex-lint SKILL: `claude --settings ~/.claude/settings.glm-4.7-flash.json -p "$(cat plugins/tools/cortex/skills/cortex-lint/SKILL.md)"`
- grep verify wiki 残留清零 (除明示排除)
- git commit (单 commit 即可, 范围小)

## Out of Scope

- 不改 `[[wikilink]]` 概念 / wikipedia URL / plugin.json keywords
- 不重命名 cortex-lint skill (它的功能名 lint 保持)
- 不动 vault 真路径 (本就无 wiki 目录, 仅字符串清理)
- 不破坏 PR1-PR5 实现 (上批 task 完成的内容)

## Technical Notes

- vault truth 来源: `.claude/memory/cortex-plugin-2026-05-13.md` §Vault 模型
- AGENT.md §协作约定 3 vault 写契约 (本任务改 AGENT.md / SKILL 走 L1 MCP 或 Edit)
- 单 sub-agent 即可完成 (机械替换 + 验证), 不需多 PR 拆分
