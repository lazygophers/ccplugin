# cortex README 用户使用说明完善

## Goal

`plugins/tools/cortex/README.md` 是用户首入口。当前 README (173 行) 计数过期 (21 skill/7 agent/17 lint/9 cli) + 缺 4 大块明细使用说明:

1. **Bash 使用说明 + 范围** (24 wrappers 全清单 + 调用方式 + 影响范围)
2. **Skills 说明 + 触发条件** (13 skill 全清单 + 自动触发关键词 + 示例)
3. **Agents 说明 + 触发** (6 agent 全清单 + 调度时机 + vs-skill 边界)
4. **定时任务说明** (9 cron 任务详细 + cron / launchd / GHA 三平台 snippet)

整改后达到"新人 5 分钟看完即能上手 + 资深用户随时查清单"。

## What I already know

- README 当前 173 行, 计数全过期 (整改前 21/7/17/9, 现 13/6/21/11)
- docs/ 已有详细文档 (Skills 详解.md / Agents.md / Commands.md / Bash 脚本.md / 周期任务.md), README 应**索引化** + **示例化**, 不重复 docs/ 全部内容
- 24 wrappers 清单已在 docs/Bash 脚本.md
- 13 skill 触发词在各 SKILL.md frontmatter description
- 9 cron 任务在 install_cron.sh + docs/周期任务.md
- 6 agent 在 agents/*.md frontmatter

## Requirements

### 必含 4 大块 (用户明示)

1. **Bash 使用说明**
   - 24 wrappers 表 (按职能分组: 安装/维护/搜索/记忆/数据 4 大组)
   - 调用方式: `bash ~/.cortex/scripts/<name>.sh` (slash 走 `claude -p "/cortex:<n> auto"`, 交互走 `--interactive`)
   - 影响范围标记 (全局 / 当前目录 / 知识库)
   - 退出码约定

2. **Skills 说明**
   - 13 skill 表 + frontmatter description 简化版 + 主要触发词
   - 触发分 3 类: 自然语言触发 / slash command 触发 / 其他 skill 内部调用
   - 渐进披露说明 (SKILL.md ≤80 行入口 + references/ 按需加载)

3. **Agents 说明**
   - 6 agent 表 + description + vs-skill 边界 (1 句话)
   - 调度时机 (并发子任务 / 长上下文隔离 / 多 source 综述等)
   - 不能直接调, 由 Claude 决策派遣

4. **定时任务说明**
   - 9 cron 任务 (lint/dashboard/digest/forget/promote/...) — 时段 + 作用 + AUTO_MODE
   - 三平台 snippet (cron / launchd / GHA)
   - 用户安装步骤 (`install_cron.sh <platform>` 复制 → 粘贴 crontab)

### 保留章节 (按现 README 升级)

- 顶部能力速览表 (计数刷新)
- 安装入口 (3 种方式)
- 配置 (vault 解析顺序)
- 5 分钟上手 (示例改用现在 13 skill)
- 故障排查 (现表保留, 个别条目刷)
- 详细文档索引 (按现 docs/ 列表刷, 删已废 skill 引用)
- License

## Acceptance Criteria

- [ ] README 顶部能力速览表计数刷新: Skills 13, Agents 6, Slash 20, Wrappers 24, Lint 18, Python CLI 11, Hooks 5
- [ ] 4 大块明细章节齐 (Bash / Skills / Agents / Cron)
- [ ] 24 wrappers 全清单含调用方式 + 影响范围
- [ ] 13 skill 全清单含触发词 + AUTO_MODE 说明 (D10)
- [ ] 6 agent 全清单含 vs-skill 边界
- [ ] 9 cron 任务全清单 + 3 平台 snippet
- [ ] 5 分钟上手示例无废 skill (canvas/new/reflect/ingest-bulk/schema/locale/forget)
- [ ] 详细文档索引列表与 docs/ 实际文件一致
- [ ] README 总行数 ≤ 400 (索引 + 示例, 不重复 docs/ 全内容)

## Definition of Done

- 计数与实际 ls 一致 (验证脚本)
- 文档同步: docs/索引.md, .claude/memory/cortex-plugin-2026-05-13.md 等保持一致 (本任务只动 README, 但需确认无冲突)
- 渲染验证: GitHub markdown 渲染 OK (表格/anchor)
- 5 分钟上手示例可复制可用

## Out of Scope

- 不动 docs/ 详细文档 (本任务仅 README)
- 不动 install.sh / wrapper 代码
- 不重复 docs/ 全部内容 (README 是入口 + 索引)
- 不写英文版 (zh-CN 单语)

## Technical Approach

整体重写 README, 按"金字塔结构": 顶部 elevator pitch (1 段) → 计数速览表 → 5 分钟示例 → 4 大块明细 → 详细文档索引 → 故障 → license。

每个明细块用表格 + 一段说明 + 1-2 示例。

## Decision (ADR-lite)

**Context**: 现 README 计数过期且缺 4 大块明细。用户首入口必须自洽且清晰。

**Decision**: 整体重写 README, 按用户明示的 4 大块 (bash/skills/agents/cron) 分章节扩展, 数据源全部 reference 实际 ls + docs/。

**Consequences**:
- ✅ 用户单文件看清"能干啥 + 怎么调 + 啥时候自动跑"
- ✅ 计数自洽, 文档索引同步
- ⚠️ README 体量从 173 → ~350 行, 但仍是索引 + 示例不是详细手册

## Technical Notes

数据源:
- 计数: `ls plugins/tools/cortex/{skills,agents,commands}/`, `ls scripts/*.sh`, `cat scripts/lint/rules.json`, `ls scripts/cli/*.py`
- Skill 触发词: 各 `skills/<name>/SKILL.md` frontmatter description
- Wrapper 调用: `scripts/install_wrappers.sh` 模板
- Cron 任务: `scripts/install_cron.sh`
- Agent 边界: `agents/<name>.md` 头部 vs-skill 注 (PR4 已加)
