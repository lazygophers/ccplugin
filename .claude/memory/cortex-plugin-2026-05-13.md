---
name: cortex-plugin
description: Cortex 插件当前真相 — vault 结构 / agent / skill / wrapper / 写契约 / 搜索契约 / 评分字段 / 记忆层
type: project
---

# Cortex 插件 — 单一真相清单

**Why**: 跨多轮重构后, cortex 的 vault 模型 / agent 集合 / preset / fold/historian 等已多次反转。本 memo 是当前真相基线, 历史变迁见 git log。

**How to apply**: 改 cortex 时以本清单为准, 旧 memory / docs 与此冲突时本清单优先。

## Vault 模型

- 单一 schema (无 preset 系统)。`_meta/version.json` 仅含 `lang` / `preserve_transcript` / `auto_commit` / `auto_push`
- 顶层: `_meta/ _templates/ _assets/ 知识库/ 记忆/ 仪表盘/ 归档/ locales/ .obsidian/ .trash/` (lint `vault-structure-violation` 强制)
- 知识库 4 子目录: `项目/<host>/<org>/<repo>/` (站点无 author 补 `_site`), `领域/{创作,学习,工作,技术,生活,金融,未分类}/`, `日记/日/<YYYY-MM>/<YYYY-MM-DD>.md`, `收件箱/`
- 记忆 L0-L4: `L0-核心/ L1-长期/ L2-中期/ L3-短期/ L4-流水账/{ledger,sessions}/ working/ views/{consolidated,candidates.md}`
- 项目路径: github/gitlab 走 `host/org/repo` 三段; 本地走相对 `$HOME`, 不足 3 段补 `_local`; website 无 author 补 `_site`
- AI 自决域: `--domain` 可选, 缺时 AI 读 body 自决 6 域, 不匹配默 `领域/未分类/`

## 资产计数

| 类型 | 计数 | 备注 |
|---|---|---|
| Agents | 7 | curator / researcher / archivist / cartographer / linker / summarizer / translator |
| Skills | 21 | 自动触发 + 显式调 |
| Slash commands | 20 | `/cortex:<name>` 冒号 |
| Wrappers | 24 | 10 slash + 3 shell + 11 CLI, 装在 `~/.cortex/scripts/*.sh` |
| Python CLI | 11 | save / search / deep_search / ingest_url / ingest_file / ingest_remote / refresh_projects / memory / ledger / session / html_render |
| Migration scripts | 2 | `migrate_scores_to_v2.py` (score 1-5 → 0-10) + `migrate_aliases_keywords_to_v3.py` (老 .md 补 aliases/keywords) — 走 `migrate.sh --to=v2\|v3` |
| Lint 规则 | 21 | 含 rule 18 `path-lang-mismatch` + rule 19 `skill-references-exists` + rule 20 `base-format-yaml` + rule 21 `frontmatter-required-scores` (4 评分字段+autofix stub) |
| Hooks | 5 | SessionStart / PostCompact / Stop / SubagentStop / UserPromptSubmit |
| Cron jobs | 9 | lint / dashboard / digest / memory-{promote,forget,compact,warden,archive} + refresh_projects (weekly Mon 03:00) |
| Tests | 548 | `cd plugins/tools/cortex/tests/python && python3 -m pytest -q` |

## Vault 写硬契约 (session_start hook 注入)

1. **L1 强制 = `mcp__obsidian__*`** (save / ingest / patch / refactor / lint --fix 等所有 vault 写)
2. **L2 fallback = 官方 `obsidian` CLI** (MCP 工具失败本次回退)
3. **L3 兜底 = 直接文件 IO** (canvas / 非 md / L1+L2 失败时)
4. **MCP 未注册** → AI 必须先 `AskUserQuestion` 单次授权 (本会话有效不写盘)
5. **未授权前**: AI 硬拒绝所有 vault 写
6. **例外**: Stop hook / cron / python CLI (非 AI 上下文) 走文件 IO

## 搜索硬契约 (user_prompt_submit hook 每轮注入)

非通用问答前, **第一个工具调用必须是搜索**:

1. **L1** `mcp__obsidian__obsidian_simple_search` (强制 first, 优先 obsidian **非 qmd**)
2. **L2** `mcp__obsidian__obsidian_complex_search` (JsonLogic tag/path 过滤)
3. **L3 fallback** `bash ~/.cortex/scripts/search.sh --query <q>` (MCP 不可达时)
4. **L4 兜底** ripgrep (search.sh 也失败时)

禁忌: 跳过搜索直问用户 / qmd 替代 obsidian / Bash rg 替代 MCP search。

## Hook 行为

- **session_start**: header + stats + L0 core + hot.md + behavior contract + triggers + collab + 🔐 Vault 写契约
- **user_prompt_submit**: **每轮注入** 🔍 搜索硬契约 (≤ 1200 字符), 触发词命中时额外加项目 hint
- **stop / postcompact**: 纯 jsonl copy 到 `记忆/L4-流水账/sessions/<cli>/<YYYY>/<MM>/<DD>/<id>.jsonl`

## 评分字段强制 (lint rule 21)

知识库 .md 强制 4 字段 (全 0.0-10.0 浮点 + maturity enum):
- `score` (内容质量) / `confidence` (AI 自信度) / `source_credibility` (源可信度, host 白名单查表) / `maturity` (draft|review|stable|deprecated)

记忆 .md 强制 2 字段: `importance` / `confidence` (0.0-10.0)。

可选 (强烈推荐, 召回率): `aliases` (≥3, 中英对+缩写) / `keywords` (≥5, path/repo/idents/headings)。

AI 自评启发式 + host_credibility 白名单 24 host: `scripts/cli/lib/remote.py` (`compute_initial_scores` / `compute_memory_scores` / `host_credibility` / `extract_aliases` / `extract_keywords`)。

详见 `skills/cortex-ingest/references/extract.md §3.1`。

### digest 双路调评分 (内联 daily cron)

- 使用信号: `log10(召回次数 + wikilink 反向引用 + 1) - 0.1 自然衰减` → importance ↑
- 反馈信号: 用户 "不对/错了" → confidence -= 1.0, "对的/正确" → confidence += 0.5
- 实现: `scripts/cli/lib/evolution.py:update_doc_scores` + digest evolution `--update-scores` 默认开

### refresh maturity 重评 (内容变, score/confidence 不动)

- hash 变 ≥ 2 + < 30 天 → draft
- 变 1 + 旧 stable → review
- 不变 ≥ 180 天 → deprecated (候选, 不实际归档)
- 不变 ≥ 90 天 → stable
- 实现: `scripts/cli/refresh_projects.py:revalue_maturity`

## hot.md 项目高分子页

save 落档时 `score ≥ 7.0 + maturity in (stable, review) + kind in (project, domain)` → 入 `hot.md ## 项目高分页面 ### <host/org/repo>` 子段, ≤ 3 / 项目 (按 score desc 排序)。

实现: `scripts/cli/save.py:_patch_hot_project_subpages`。

## Ingest 项目级硬契约 (SKILL §1.1 / §7 / §8 / §9)

- **4 层目录** (`知识库/项目/<host>/<org>/<repo>/`): `主题/` (架构/决策/陷阱/依赖/配置/错误码/测试/功能 ≥4) + `模块/` + `文件/` + `符号/api/`
- **分级 .md 下限**: ≤50 文件 ≥15 .md / 50-500 ≥40 / >500 ≥100
- **6 类抽取**: API surface + 配置 schema + 错误码 + 测试 + 功能 + 全局常量
- **强制排除**: build 产物 / lock / binary / 系统 IDE / 临时备份 / 压缩包
- **知识图谱 4 制品**: `_db.base` (Bases YAML, **非 markdown/DQL**, lint rule 20 强制) + `_assets/canvases/<repo>.canvas` (≤20 节点) + Wikilink 网 (每 .md 出链 ≥5) + websearch 扩展
- **拒交**: 4 层任一空 / 6 类任一缺 / ALL_MD < 下限 / M/R < 0.8 → AI 必须继续补

## 远程 ingest + 批量增量 refresh

- `bash ~/.cortex/scripts/ingest_remote.sh <url>` — github/gitlab clone + website crawl (sitemap → BFS, depth ≤3) → `知识库/项目/<host>/<org>/<repo or _site/slug>/`
- `bash ~/.cortex/scripts/refresh_projects.sh [--scope=<host/org/repo>]` — 扫全 `知识库/项目/`, 仅增量 (git diff sha / website hash 对比)
- 增量元数据 (frontmatter): `source_url` / `source_type` (github|gitlab|website) / `last_ingested_at` / `last_commit_sha` (git) / `content_hash` (website 每页)
- weekly cron Mon 03:00 自动跑 refresh_projects

## Digest 路由识别 (SKILL §2-§3-§5)

- **6 信号** repo 归属: frontmatter `host/org/repo` (强) > `source_url` (强) > wikilink (中) > URL (中) > tag (中) > keyword ≥3 (弱)
- **路由**: 反思/连接/矛盾/决策 4 类命中 repo 落 `知识库/项目/<host>/<org>/<repo>/笔记/`, 未命中 fallback `知识库/收件箱/`
- 多 repo: 强信号优先 + 其他 repo 加 backlink
- **第 6 阶段 evolution**: 抽 sessions 复发 pattern → `记忆/L0-核心/patterns.md` (semantic, 6 category) → 生 `_assets/evolution-proposals/<date>-<slug>.md` proposal → cortex-refactor `evolution-apply` 用户 AskUserQuestion 确认 patch
- 阈值: 硬编码 `MIN_CONFIDENCE=0.8 AND MIN_APPLICATIONS=3`
- §5 清理: 收件箱 ≥30 天复扫迁项目/笔记/, 否则归档

## 关键约定

- AUTO_MODE persistent (禁询问 ≠ 中止, AI 自决循环修复至 clean)
- Frontmatter `tags` ≥10 强制 (lint `fm-missing-tags` autofix 派生 12 维度, 严禁占位符)
- Banned fm fields: `preset` (已废)
- 路径 lang 校验 (rule 18): vault.lang=zh-CN segment 全 ASCII 或 lang=en segment 含 CJK → warn; 豁免 host/org/repo + ASCII 专名 + frontmatter `path_lang_exempt: true`
- cortex-refactor 子操作: `rename` / `merge` / `split` / `evolution-apply` (proposal → AskUserQuestion → patch SKILL/AGENT, safety gate 白名单 skills/agents/AGENT.md, 黑名单 commands/scripts/_meta/_templates, git clean 必)
- 插件路径硬编码 `$HOME/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex`
- 自研 MCP 已移除, 走官方 `mcp-obsidian`
- Slash wrapper: `-h`/`--help` + `-i`/`--interactive` + `--no-commit`; 调 claude 时 echo bash + `--dangerously-skip-permissions`
- patterns / aliases/keywords / score 字段 migration: `bash ~/.cortex/scripts/migrate.sh --to=v2|v3`

## 关联 docs

- `plugins/tools/cortex/AGENT.md` §1 搜索硬契约 / §3 vault 写契约权威
- `plugins/tools/cortex/docs/{知识库结构,Agents,Commands,Skills 详解,Hooks 机制,Lint 规则,安装与配置,快速上手,故障排查}.md`
- `plugins/tools/cortex/scripts/lint/schemas.py` — vault 单一 schema
- `plugins/tools/cortex/skills/cortex-ingest/references/{layout,extract,exclude,knowledge-graph}.md` — ingest 4 层 + 6 类抽取 + 排除 + KG 4 制品 + 评分字段启发式
- `plugins/tools/cortex/skills/cortex-memory/references/scoring.md` — 记忆 2 字段 + L0-L4 默认 + digest 双路规则

历史变迁 (P5-P10 详细叙事): 见 git log + `.trellis/tasks/archive/2026-05/`。
